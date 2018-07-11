from collections import defaultdict

import torch

from ..data import Row
from .modules import Hidden2Normal, InputEmbedding


def one_cold(i, n):
    """Inverse one-hot encoding."""
    x = torch.ones(n, dtype=torch.uint8)
    x[i] = 0
    return x


class OccupancyPooling(torch.nn.Module):
    def __init__(self, cell_side=0.5, n=6, hidden_dim=128):
        super(OccupancyPooling, self).__init__()
        self.cell_side = cell_side
        self.n = n
        self.hidden_dim = hidden_dim

        self.embedding = torch.nn.Linear(n * n, hidden_dim)

    def forward(self, _, __, obs):
        occupancies = self.occupancies(obs)
        return self.embedding(occupancies)

    def occupancies(self, obs):
        n = obs.size(0)
        return torch.stack([
            self.occupancy(obs[i], obs[one_cold(i, n)])
            for i in range(n)
        ], dim=0)

    def occupancy(self, xy, other_xy):
        """Returns the occupancy."""
        if xy[0] != xy[0] or \
           other_xy.size(0) == 0:
            return torch.zeros(self.n * self.n)

        oxy = other_xy[torch.isnan(other_xy[:, 0]) == 0]
        if not oxy.shape[0]:
            return torch.zeros(self.n * self.n)

        oij = ((oxy - xy) / self.cell_side + self.n / 2)
        range_violations = torch.sum((oij < 0) + (oij >= self.n), dim=1)
        oij = oij[range_violations == 0, :].long()
        if oij.shape[0] == 0:
            return torch.zeros(self.n * self.n)
        oi = oij[:, 0] * self.n + oij[:, 1]
        occ = torch.zeros(self.n * self.n)
        occ[oi] = 1

        return occ