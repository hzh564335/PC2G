"""Module candidates; these are adaptations, not claims of replicated module papers."""
import torch
from torch import nn
import torch.nn.functional as F


class PseudoDistributionAlignment(nn.Module):
    """ReMixMatch distribution alignment adapted to a frozen MSDGN label budget.

    Reference: Google LLC, remixmatch_no_cta.py and libml/layers.py, commit
    f7061ebf055227cbeb5c6fced1ce054e0ceecfcd (Apache-2.0; LICENSE_ReMixMatch.txt).
    Implements only distribution alignment and its 128-batch moving average,
    without ReMixMatch sharpening, augmentations, mixup or model-weight EMA.
    """
    def __init__(self, classes, window=128):
        super().__init__()
        self.register_buffer('history', torch.full((window, classes), 1. / classes))
        self.register_buffer('prior', torch.full((classes,), 1. / classes))
        self.register_buffer('updates', torch.zeros((), dtype=torch.long))

    @torch.no_grad()
    def set_labeled_prior(self, labels):
        counts = torch.bincount(labels, minlength=len(self.prior)).to(self.prior)
        if counts.shape != self.prior.shape or not torch.all(counts > 0):
            raise ValueError('All classes must occur in the labeled source prior')
        self.prior.copy_(counts / counts.sum())

    @torch.no_grad()
    def forward(self, logits):
        # Use the PREVIOUS history for this step, as in the upstream post-update.
        marginal = self.history.mean(0)
        marginal = marginal / marginal.sum()
        # Log-space form of p*(prior+eps)/(marginal+eps), then row renormalization
        # by selected_indices' softmax. No underflow-induced log(0) is introduced.
        adjusted = logits.detach() + (self.prior + 1e-6).log() - (marginal + 1e-6).log()
        if self.training:
            entry = logits.detach().softmax(1).mean(0, keepdim=True)
            self.history.copy_(torch.cat((self.history[1:], entry), dim=0))
            self.updates.add_(1)
        return adjusted


class ResidualASB(nn.Module):
    """TSLANet ASB adapted to B,C,L after the first CNN block, with residual preservation.

    Reference: https://github.com/emadeldeen24/TSLANet (ICML 2024).
    Same energy/median mask and straight-through threshold estimator; local wrapper
    adds the spectral correction to its input and initializes complex weights small.
    """
    def __init__(self, channels):
        super().__init__()
        self.weight = nn.Parameter(torch.empty(channels, 2))
        self.weight_high = nn.Parameter(torch.empty(channels, 2))
        nn.init.trunc_normal_(self.weight, std=.02)
        nn.init.trunc_normal_(self.weight_high, std=.02)
        self.threshold = nn.Parameter(torch.rand(1))

    def forward(self, x):
        z = torch.fft.rfft(x.float().transpose(1, 2).contiguous(), dim=1, norm='ortho')
        energy = z.abs().square().sum(-1)
        relative = energy / (energy.median(dim=1, keepdim=True).values + 1e-6)
        mask = ((relative > self.threshold).float() - self.threshold).detach() + self.threshold
        filtered = z * torch.view_as_complex(self.weight.contiguous())
        filtered = filtered + z * mask.unsqueeze(-1) * torch.view_as_complex(self.weight_high.contiguous())
        correction = torch.fft.irfft(filtered, n=x.shape[-1], dim=1, norm='ortho').transpose(1, 2)
        return x + correction.to(x.dtype)


def paired_consistency(clean_features, altered_features):
    """Fixed mild feature-statistics perturbation plus paired consistency screening.

    Inspired by BDC's consistency motivation, but NOT BDC reproduction: there is
    no auxiliary teacher, learned perturbation game or original complete loss.
    Name in output remains 'stat_consistency', never 'BDC'.
    """
    return (F.normalize(clean_features.detach(), dim=1) -
            F.normalize(altered_features, dim=1)).square().sum(dim=1).mean()


def statistic_perturbation(x, generator):
    # Applied to first-layer nonnegative features. Positive gain preserves sign.
    scale = torch.randn((len(x), x.shape[1], 1), device=x.device, generator=generator) * .1
    shift = torch.randn(scale.shape, device=x.device, generator=generator) * .1
    std = x.std(-1, keepdim=True).detach().clamp_min(1e-5)
    return x * scale.exp() + shift * std
