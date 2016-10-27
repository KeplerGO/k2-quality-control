import numpy as np
import matplotlib.pyplot as pl
import seaborn as sns
from astropy.io import fits
import click


def plot_flux(tpf_path, output_fn, max_quality=0):
    f = fits.open(tpf_path)

    cadence = f[1].data['CADENCENO']
    mask_quality = f[1].data['QUALITY'] <= max_quality
    np.seterr(invalid='ignore')
    flux = np.nansum(f[1].data['FLUX'], axis=(1, 2))
    bg = np.nansum(f[1].data['FLUX_BKG'], axis=(1, 2))
    raw = np.nansum(f[1].data['RAW_CNTS'], axis=(1, 2))

    pl.figure(figsize=(8, 8))

    ax = pl.subplot(411)
    ax.set_title(tpf_path)
    ax.scatter(cadence[mask_quality], raw[mask_quality], c='blue', lw=0)
    ax.set_xlim([cadence[0] - 10, cadence[-1] + 10])
    ax.set_ylabel('RAW_CNTS')

    ax = pl.subplot(412)
    ax.scatter(cadence[mask_quality], bg[mask_quality], c='blue', lw=0)
    ax.set_xlim([cadence[0] - 10, cadence[-1] + 10])
    ax.set_ylabel('FLUX_BKG')

    ax = pl.subplot(413)
    ax.scatter(cadence[mask_quality], flux[mask_quality], c='blue', lw=0)
    ax.set_xlim([cadence[0] - 10, cadence[-1] + 10])
    ax.set_ylabel('FLUX')

    mean = np.nanmean(flux[mask_quality])
    sigma = np.nanstd(flux[mask_quality])
    mask_outliers = flux[mask_quality] > (mean + 6*sigma)
    for idx in np.argwhere(mask_outliers):
        pl.text(cadence[mask_quality][idx], flux[mask_quality][idx], cadence[mask_quality][idx][0], fontsize=10)

    ax = pl.subplot(414)
    ax.scatter(cadence[mask_quality], flux[mask_quality], c='blue', lw=0)
    ax.set_ylim([mean - 3*sigma, mean + 3*sigma])
    ax.set_xlim([cadence[0] - 10, cadence[-1] + 10])
    ax.set_ylabel('FLUX')

    ax.set_xlabel('CADENCENO')

    pl.tight_layout()
    pl.savefig(output_fn, dpi=200)
    pl.close()


@click.command()
@click.argument('path', type=click.Path(exists=True))
def k2qc_flux_main(path):
    """Plots the FLUX, FLUX_BKG, and RAW_CNTS time series given a Target Pixel File."""
    output_fn = 'k2qc-flux.png'
    print('Writing {}'.format(output_fn))
    plot_flux(path, output_fn)
