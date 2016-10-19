from astropy.io import fits
import click
import numpy as np
import pandas as pd
import matplotlib.pyplot as pl

# The meaning of the various flags are described in the Kepler Archive Manual
KEPLER_QUALITY_FLAGS = {
    "1": "Attitude tweak",
    "2": "Safe mode",
    "4": "Coarse point",
    "8": "Earth point",
    "16": "Zero crossing",
    "32": "Desaturation event",
    "64": "Argabrightening",
    "128": "Cosmic ray",
    "256": "Manual exclude",
    "1024": "Sudden sensitivity dropout",
    "2048": "Impulsive outlier",
    "4096": "Argabrightening",
    "8192": "Cosmic ray",
    "16384": "Detector anomaly",
    "32768": "No fine point",
    "65536": "No data",
    "131072": "Rolling band",
    "262144": "Rolling band",
    "524288": "Possible thruster firing",
    "1048576": "Thruster firing"
}


def quality_flags(quality):
    """Converts a Kepler/K2 QUALITY integer into human-readable flags.

    This function takes the QUALITY bitstring that can be found for each
    cadence in Kepler/K2's pixel and light curve files and converts into
    a list of human-readable strings explaining the flags raised (if any).

    Parameters
    ----------
    quality : int
        Value from the 'QUALITY' column of a Kepler/K2 pixel or lightcurve file.

    Returns
    -------
    flags : list of str
        List of human-readable strings giving a short description of the
        quality flags raised.  Returns an empty list if no flags raised.
    """
    flags = []
    for flag in KEPLER_QUALITY_FLAGS.keys():
        if quality & int(flag) > 0:
            flags.append(KEPLER_QUALITY_FLAGS[flag])
    return flags


def get_quality_flags_summary(path):
    f = fits.open(path)
    summary = []
    for flag in KEPLER_QUALITY_FLAGS.keys():
        flag_count = ((f[1].data['QUALITY'] & int(flag)) > 0).sum()
        summary.append({'flag': KEPLER_QUALITY_FLAGS[flag],
                        'bit': int(np.log2(int(flag))),
                        'value': int(flag),
                        'count': flag_count})
    df = pd.DataFrame(summary)
    df.first_cadence = f[1].data['CADENCENO'][0]
    df.last_cadence = f[1].data['CADENCENO'][-1]
    df.total_cadence_count = len(f[1].data['CADENCENO'])
    return df


def plot_quality_flags(path, output_fn):
    """Plots a graphical overview of quality flags vs cadence number."""
    f = fits.open(path)
    pl.figure(figsize=(16, 9))

    cadenceno = f[1].data['CADENCENO']
    labels = []
    bits = range(len(KEPLER_QUALITY_FLAGS))
    for bit in bits:
        flag = int(2**bit)
        if str(flag) not in KEPLER_QUALITY_FLAGS:
            labels.append('')
            continue
        flag_mask = (f[1].data['QUALITY'] & int(flag)) > 0
        pl.scatter(cadenceno[flag_mask], [bit]*flag_mask.sum(), marker='|')
        labels.append(KEPLER_QUALITY_FLAGS[str(flag)])
    pl.xlim([cadenceno[0], cadenceno[-1]])
    pl.ylim([-1, len(KEPLER_QUALITY_FLAGS)+1])
    pl.xlabel('Cadence')
    pl.yticks(bits, labels)
    pl.tight_layout()
    pl.savefig(output_fn)
    pl.close()


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--plot', is_flag=True)
def k2qc_flags_main(path, plot):
    """Show a summary of the QUALITY flags."""
    df = get_quality_flags_summary(path)
    print('First cadence: {}'.format(df.first_cadence))
    print('Last cadence: {}'.format(df.last_cadence))
    print('Total number of cadences: {}'.format(df.total_cadence_count))
    print(df.sort_values('value')
            .to_string(columns=['bit', 'value', 'flag', 'count'], index=False))
    if plot:
        output_fn = 'k2qc-flags.png'
        print('Writing {}'.format(output_fn))
        plot_quality_flags(path, output_fn)


if __name__ == '__main__':
    example_quality = 1089568
    print(quality_flags(example_quality))
