"""Verify Kepler/K2 Target Pixel Files."""
import click
import glob
import os
import re
from tqdm import tqdm
import numpy as np
import warnings

from astropy.io import fits
from astropy.wcs import WCS


class QualityIssueLogger(object):
    """Log quality control issues.
    """
    def __init__(self):
        self.issues = []
        self.tpf_files_checked = 0

    def report_issue(self, filename, issue):
        msg = '{}: {}'.format(filename, issue)
        print(msg)
        self.issues.append(msg)

    def record_issues(self):
        with open('issues.txt', 'w+') as rec:
            for issue in self.issues:
                rec.write("{}\n".format(issue))

    def print_summary(self):
        print('Found {} issues ({} files checked).'.format(len(self.issues),
                                                           self.tpf_files_checked))


class TargetPixelFileValidator(object):
    """Verify the quality of a Kepler/K2 Target Pixel File.
    """
    def __init__(self, issue_logger):
        self.log = issue_logger

    def validate(self, tpf_filename):
        """Validate a single Kepler/K2 Target Pixel File."""
        self.tpf_filename = tpf_filename
        self.tpf = fits.open(tpf_filename)
        # Use introspection to identify all verification methods
        verification_methods = [method for method in dir(self)
                                if method.startswith('verify')]
        for verification in verification_methods:
            try:
                getattr(self, verification)()
            except AssertionError:
                self.log.report_issue(self.tpf_filename, verification)
        self.tpf.close()
        self.log.tpf_files_checked += 1

    def verify_fits_standard(self):
        """Call astropy.io.fits.verify() to verify FITS file integrity."""
        try:
            self.tpf.verify(option='exception')
        except Exception:
            assert False

    def verify_table_shapes(self):
        """The binary tables should have consistent data shapes."""
        assert self.tpf[1].data['TIME'].shape == self.tpf[1].data['TIMECORR'].shape
        assert self.tpf[1].data['TIME'].shape == self.tpf[1].data['CADENCENO'].shape
        assert self.tpf[1].data['TIME'].shape[0] == self.tpf[1].data['FLUX'].shape[0]
        assert self.tpf[1].data['FLUX'].shape == self.tpf[1].data['FLUX_ERR'].shape
        assert self.tpf[1].data['FLUX'].shape == self.tpf[1].data['RAW_CNTS'].shape
        assert self.tpf[1].data['FLUX'].shape == self.tpf[1].data['FLUX_BKG'].shape
        assert self.tpf[1].data['FLUX'].shape == self.tpf[1].data['FLUX_BKG_ERR'].shape

    def verify_aperture_img(self):
        """The aperture image should not be empty."""
        assert self.tpf['APERTURE'].data.sum() > 0

    def verify_aperture_img_shape(self):
        """Flux data shape should match the aperture image shape.
        This is a regression test for KSOC-5085)."""
        assert self.tpf[1].header['TDIM5'] == '({},{})'.format(self.tpf[2].header['NAXIS1'],
                                                               self.tpf[2].header['NAXIS2'])

    def verify_thruster_flags(self):
        """K2 Campaigns 3 and later should contain sensible Thruster Firing Flags.

        K2 Campaigns 0-1-2 should be reprocessed by end 2016 to include the same.
        """
        THRUSTER_FIRING_FLAG = 1048576
        # Campaigns 9a (91), 9b (92), 10a (101) are "Type 1" Target Pixel Files
        # that do not have thruster firing flags set.
        CAMPAIGNS_WITHOUT_THRUSTER_FLAGS = [91, 92, 101]
        if ('CAMPAIGN' in self.tpf[0].header and
                self.tpf[0].header['CAMPAIGN'] not in CAMPAIGNS_WITHOUT_THRUSTER_FLAGS):
            thruster_firings = ((self.tpf[1].data['QUALITY'] & THRUSTER_FIRING_FLAG) > 0).sum()
            campaign_length = self.tpf[1].header['TELAPSE']  # days
            # Expect at least one thruster firing per day
            assert thruster_firings > campaign_length

    def verify_quality_flags(self):
        """At least some cadences should have QUALITY FLAGS equal to 0 (i.e. perfect data)."""
        assert (self.tpf[1].data['QUALITY'] == 0).sum() > 0

    def verify_wcs_keywords(self):
        """Are the WCS keywords valid?"""
        try:
            WCS(self.tpf[2].header)
        except Exception:
            assert False

    def verify_wcs_coordinates(self):
        """Is the WCS solution consistent with RA_OBJ and DEC_OBJ?"""
        w = WCS(self.tpf[2].header)
        # TODO: verify that the order of NAXIS1 vs NAXIS2 is correct, prob transposed
        ra, dec = w.all_pix2world([[self.tpf[2].header['NAXIS1']/2.,
                                    self.tpf[2].header['NAXIS2']/2.]],
                                  0)[0]
        assert np.abs(ra - self.tpf[0].header['RA_OBJ']) < 0.1  # degrees
        assert np.abs(dec - self.tpf[0].header['DEC_OBJ']) < 0.1  # degrees

    def verify_positive_flux(self):
        """The observed flux (inc background) should never be negative."""
        # Channel 43 (Mod.out 13.3) contains bad columns at col < 100 which
        # will lead to aberrant fluxes; ignore this region
        if self.tpf[0].header['CHANNEL'] == 43 and self.tpf[2].header['CRVAL1P'] < 100:
            return
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # ignore NaN comparison warnings
            mask = self.tpf[1].data['QUALITY'] == 0
            flux_plus_bkg = (self.tpf[1].data['FLUX'] + self.tpf[1].data['FLUX_BKG'])
            if ((flux_plus_bkg < 0).sum(axis=(1, 2))[mask]).sum() > 0:
                badpixels = np.argwhere(flux_plus_bkg < 0)
                for pix in badpixels:
                    if mask[pix[0]]:
                        print("FLUX + FLUX_BKG < 0 found at frame {}, pixel "
                              "coordinates ({},{})".format(pix[0], pix[1], pix[2]))
                assert False

    def verify_cdpp(self):
        """Are the CDPP estimates sensible?."""
        CDPP_KEYWORDS = ['CDPP3_0', 'CDPP6_0', 'CDPP12_0']
        try:
            for kw in CDPP_KEYWORDS:
                assert float(self.tpf[1].header[kw]) > 0
            if float(self.tpf[0].header['KEPMAG']) < 15:
                for kw in CDPP_KEYWORDS:
                    # Expect at least 1% photometry for bright stars
                    assert float(self.tpf[1].header[kw]) < 10000
        except TypeError:
            return   # Ignore custom masks without target

    def verify_campaign_number(self):
        """Does campaign number in filename match the CAMPAIGN header keyword?"""
        if self.tpf[0].header['MISSION'] != 'Kepler':
            campaign_from_header = int(self.tpf[0].header['CAMPAIGN'])
            campaign_from_filename = int(re.findall(r'\d+', self.tpf_filename)[-1])
            assert campaign_from_header == campaign_from_filename


class KeplerQualityPolice(object):

    def __init__(self):
        self.logger = QualityIssueLogger()

    def check_path(self, path, record_issues=True):
        """
        Parameters
        ----------
        directory : str
            Path to a directory containing Target Pixel Files.
        """
        validator = TargetPixelFileValidator(self.logger)
        filenames = (glob.glob(os.path.join(path, '*-targ.fits'))
                     + glob.glob(os.path.join(path, '*-targ.fits.gz')))
        for filename in tqdm(filenames, desc='Checking Target Pixel Files'):
            validator.validate(filename)
        self.logger.print_summary()

        if record_issues:
            self.logger.record_issues()



@click.command()
@click.argument('path', type=click.Path(exists=True))
def k2qc_main(path):
    """Check Kepler/K2 data for errors.

    PATH must be the location of a Kepler/K2 Target Pixel File,
    or a directory containing such Target Pixel Files."""
    KeplerQualityPolice().check_path(path)


if __name__ == '__main__':
    k2qc_main()  # Call the command-line function
