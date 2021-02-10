from streaking.gaussian_beam import SimpleGaussianBeam
from streaking.time_energy_map import Time_Energy_Map
from streaking.ionization import ionizer_simple, ionizer_Sauter
from streaking.conversions import cartesian_to_spherical
from streaking.streak import classical_lorentz_streaker
import numpy as np
import scipy.stats
import scipy.constants as const
from matplotlib.widgets import Slider
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("GTK3Agg")


if __name__ == "__main__":
    """
    XFEL_intensity = lambda t: (
        0.6 * scipy.stats.norm(0, 1e-15).pdf(t)
        + 0.4 * scipy.stats.norm(3e-15, 2e-15).pdf(t)
    )

    XFEL_photon_energy = scipy.stats.norm(1200, 0.1).pdf

    pe = ionizer_simple(
        2,  # β
        XFEL_intensity,
        XFEL_photon_energy,
        870.2,  # binding energy
        (1190, 1210),  # considered energy range
        (-5e-14, 7e-14),  # considered time range
        5000,  # number of electrons to generate (not yet based on cross section)
    )"""
    N_G = 5

    mu_t = np.random.normal(0, 1.5e-15, N_G)  # s
    mu_E = np.random.normal(1200, 2, N_G)  # eV
    sigma_t = np.abs(np.random.normal(0.4e-15, 0.2e-15, N_G))
    sigma_E = np.abs(np.random.normal(2, 0.5, N_G))
    corr_list = np.random.normal(0, 0, N_G)
    I_list = np.abs(np.random.normal(10, 0.1, N_G))
    stepsizes = (1e-16, 0.1)

    TEmap = Time_Energy_Map(
        mu_list=np.stack((mu_t, mu_E)),
        sigma_list=np.stack((sigma_t, sigma_E)),
        corr_list=corr_list,
        I_list=I_list,
        stepsizes=stepsizes,
    )

    N_e = 2000
    E_ionize = 900  # eV

    pe = ionizer_Sauter(TEmap, E_ionize, N_e)

    beam = SimpleGaussianBeam(energy=30e-6, cep=0)
    spe = classical_lorentz_streaker(pe, beam, (0, 1e-12), 1e-14)

    r, phi, theta = cartesian_to_spherical(*pe.p.T)
    sr, sphi, stheta = cartesian_to_spherical(*spe.p.T)

    fig = plt.figure(constrained_layout=True)
    gs = gridspec.GridSpec(6, 2, height_ratios=[10, 20, 1, 1, 1, 1], figure=fig)
    ax0 = plt.subplot(gs[0, :])
    ax0.set_xlabel("$t$ / fs")
    ax0.set_ylabel(r"$h\nu$ / eV")
    ax0.pcolormesh(
        TEmap.time_list * 1e15,
        TEmap.Ekin_list,
        TEmap.time_energy_map,
        shading="nearest",
    )
    ax1 = plt.subplot(gs[1, 0])

    bins = [np.linspace(0, 2 * np.pi, 51), 50]

    # Create 2d Histogram
    data, x, y = np.histogram2d(
        (theta + np.pi / 2) % (2 * np.pi), pe.Ekin() / const.e, bins=bins
    )
    im1 = ax1.imshow(data.T, origin="lower", aspect="auto")
    im1.set_extent((x[0], x[-1], y[0], y[-1]))
    # plt.hist2d(pe.p.T[0], pe.p.T[1], bins=200)
    ax1.set_title("Unstreaked")
    ax2 = plt.subplot(gs[1, 1])
    ax2.set_title("Streaked")
    data, x, y = np.histogram2d(
        (stheta + np.pi / 2) % (2 * np.pi), spe.Ekin() / const.e, bins=bins
    )
    im2 = ax2.imshow(data.T, origin="lower", aspect="auto")
    im2.set_extent((x[0], x[-1], y[0], y[-1]))

    for ax in (ax1, ax2):
        ax.set_xlabel(r"$\varphi$")
        ax.set_ylabel(r"$E_\mathrm{kin}$ / eV")

    def update(val):
        # Change arguments and calculate new trajectories
        beam = SimpleGaussianBeam(energy=s0.val, cep=s1.val)
        spe = classical_lorentz_streaker(pe, beam, (0, s2.val), s3.val)
        r, phi, theta = cartesian_to_spherical(*pe.p.T)
        sr, sphi, stheta = cartesian_to_spherical(*spe.p.T)
        data, x, y = np.histogram2d(
            (theta + np.pi / 2) % (2 * np.pi), pe.Ekin() / const.e, bins=bins
        )
        im1.set_data(data.T)
        im1.set_extent((x[0], x[-1], y[0], y[-1]))
        data, x, y = np.histogram2d(
            (stheta + np.pi / 2) % (2 * np.pi), spe.Ekin() / const.e, bins=bins
        )
        im2.set_data(data.T)
        im2.set_extent((x[0], x[-1], y[0], y[-1]))

    # Create three slider axes to modify α0-α2 on the fly
    slax0, slax1, slax2, slax3 = (
        plt.subplot(gs[2, :]),
        plt.subplot(gs[3, :]),
        plt.subplot(gs[4, :]),
        plt.subplot(gs[5, :]),
    )
    s0 = Slider(slax0, r"Energy", 0, 30e-6, valfmt="%.1e", valinit=30e-6)
    s1 = Slider(slax1, r"CEP", 0, 2 * np.pi, valfmt="%.1e", valinit=0)
    s2 = Slider(slax2, r"time", 0, 1e-11, valfmt="%.1e", valinit=1e-12)
    s3 = Slider(slax3, r"step", 0.5e-14, 2e-14, valfmt="%.1e", valinit=1e-14)
    for s in (s0, s1, s2, s3):
        s.valtext.set_fontfamily("monospace")
        s.on_changed(update)

    plt.show()
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection="3d")
    # ax.plot(E[..., 0], E[..., 1], z * 1e6)
    # ax.set_xlabel(r"$E_x$ / Vm$^{-1}$")
    # ax.set_ylabel(r"$E_y$ / Vm$^{-1}$")
    # ax.set_zlabel(r"$z$ / µm")
    # plt.show()
