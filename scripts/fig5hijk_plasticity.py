"""
Simulate effect of increased LTD
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.constants import pink, green
from src import constants
from src.constants import lr, control_th, increased_th, min_th, max_th, Tplasticity
from src.constants import figdir, stylesheet
from src.simulation import bcm_update, simulate_with_plasticity
from src.metrics import compute_osi
from src.utils import write_excel

# Added code to plot with Arial font in Windows
import matplotlib
from matplotlib import rc
matplotlib.rcParams['pdf.fonttype'] = 42
rc('font', **{'family': 'serif', 'serif': ['Arial']})

sns.set_context("poster")
sns.set_palette("colorblind")
plt.style.use(stylesheet)

# collecting/saving data:
save_path = "results/Source Data Fig. 5.xlsx"
data_frames = {}
for panel in ['h', 'i', 'j', 'k']:
    data_frames[panel] = pd.DataFrame()

fig, ax = plt.subplots(1, 4, figsize=(5.1, 1.3), sharey=False)

# Show the plasticity rule
pre = 1
post = np.arange(0, 20, 0.1)
theta_lo, theta_hi = 7, 12  # Just examples to illustrate rule
ax[0].plot(post, bcm_update(pre, post, theta_lo), color=pink)
ax[0].plot(post, bcm_update(pre, post, theta_hi), color=green)
data_frames['h']['Post'] = post
data_frames['h']['Delta W'] = bcm_update(pre, post, theta_lo)
data_frames['h']['Delta W LTD'] = bcm_update(pre, post, theta_hi)
ax[0].hlines(0, post[0], post[-1], colors="black", linestyles=":")
ax[0].set_ylim([-0.5, 1])
ax[0].set_ylabel("Synaptic change")
ax[0].set_xlabel("PV rate (1/s)")
# Add threshold
ax[0].annotate(
    "",
    xy=(theta_lo, 0),
    xycoords="data",
    xytext=(theta_lo, 0.4),
    textcoords="data",
    arrowprops=dict(arrowstyle="->", lw=0.5, connectionstyle="arc3", color="gray"),
)
ax[0].text(3, 0.4, "Threshold", color="gray", rotation=0)
ax[0].tick_params(axis='both', which='major', labelsize=5)

# Simulate it
ex_thresholds = [control_th, increased_th]
for i, (threshold, color) in enumerate(zip(ex_thresholds, [pink, green])):
    stimuli, pre_rates, rates, weights = simulate_with_plasticity(
        threshold=threshold, learning_rate=lr, T=Tplasticity, mean_scaling=True
    )

    ax[2].plot(stimuli, rates[-1], color=color)
    ax[1].plot(weights[-1], color=color)
    data_frames['i']['stimulus'] = stimuli[::2]
    data_frames['j']['stimulus'] = stimuli
    data_frames['i'][f'weights {threshold}'] = weights[-1]
    data_frames['j'][f'rates {threshold}'] = rates[-1]

    # Test convergence
    assert np.allclose(np.abs(np.diff(rates[-100:], axis=0) ** 2), 0)
    assert np.allclose(np.abs(np.diff(weights[-100:], axis=0) ** 2), 0)

for i in [1, 2]:
    if i == 1:
        labels = np.array([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
        ticks = np.linspace(0, constants.n_pre, 5)
        ax[i].set_xticks(ticks, np.array(labels * 180 / np.pi, dtype=int))
    else:
        ticks = np.array([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
        ax[i].set_xticks(ticks, np.array(ticks * 180 / np.pi, dtype=int))
    ax[i].set_xlabel(r"Stim. direction (Δ°)")

ax[2].set_yticks([0, 5, 10, 15])
ax[2].set_ylabel("Rate (1/s)")
ax[1].set_ylabel("Weight")
ax[1].tick_params(axis='both', which='major', labelsize=5)
ax[2].tick_params(axis='both', which='major', labelsize=5)

print("LTD threshold : OSI")
thresholds = np.arange(min_th, max_th, dtype=float, step=0.25)
osis = np.zeros((len(thresholds),))
for i, threshold in enumerate(thresholds):
    stimuli, pre_rates, rates, weights = simulate_with_plasticity(
        threshold=threshold, learning_rate=lr, T=Tplasticity, mean_scaling=True
    )
    osis[i] = compute_osi(stimuli, rates[-1])
    if threshold in ex_thresholds:
        print(f"{threshold:0.2f}: {osis[i]:0.2f}*")
    # Test convergence
    assert np.allclose(np.abs(np.diff(rates[-100:], axis=0) ** 2), 0)
    assert np.allclose(np.abs(np.diff(weights[-100:], axis=0) ** 2), 0)

data_frames['k']['treshold'] = thresholds
data_frames['k']['OSI'] = osis
ax[3].plot(thresholds, osis, color="gray")
for th, color in zip(ex_thresholds, [pink, green]):
    i = np.argmin(np.abs(thresholds - th))
    ax[3].scatter(
        thresholds[i],
        osis[i],
        color=color,
    )
ax[3].set_ylim([0.3, 0.8])
ax[3].set_yticks([0.4, 0.6, 0.8])
ax[3].set_ylabel("Selectivity (OSI)")
ax[3].set_xlabel("Threshold (1/s)")
ax[3].tick_params(axis='both', which='major', labelsize=5)

fig.tight_layout()
plt.savefig(figdir + "fig5hijk_plasticity.png", dpi=300)
# Export to PDF too
plt.savefig(figdir + "fig5hijk_plasticity.pdf", dpi=300)

write_excel(save_path, data_frames)
