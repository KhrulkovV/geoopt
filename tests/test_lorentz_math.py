import torch
import random
import numpy as np
import pytest
from geoopt.manifolds import lorentz

@pytest.fixture("function", autouse=True, params=range(30, 40))
def seed(request):
    seed = request.param
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    return seed


@pytest.fixture("function", params=[torch.float64, torch.float32])
def dtype(request):
    return request.param


@pytest.fixture
def k(seed, dtype):
    # test broadcasted and non broadcasted versions
    return torch.Tensor([1. + 1e-10])


@pytest.fixture
def a(seed, k):
    if seed > 35:
        # do not check numerically unstable regions
        # I've manually observed small differences there
        a = torch.empty(100, 10, dtype=k.dtype).normal_(-1, 1)
        a /= a.norm(dim=-1, keepdim=True) * 1.3
        a *= (torch.rand_like(k) * k) ** 0.5
    else:
        a = torch.empty(100, 10, dtype=k.dtype).normal_(-1, 1)
        a /= a.norm(dim=-1, keepdim=True) * 1.3
        a *= random.uniform(0, k) ** 0.5
    return lorentz.math.project(a, k=k)


@pytest.fixture
def b(seed, k):
    if seed > 35:
        b = torch.empty(100, 10, dtype=k.dtype).normal_(-1, 1)
        b /= b.norm(dim=-1, keepdim=True) * 1.3
        b *= (torch.rand_like(k) * k) ** 0.5
    else:
        b = torch.empty(100, 10, dtype=k.dtype).normal_(-1, 1)
        b /= b.norm(dim=-1, keepdim=True) * 1.3
        b *= random.uniform(0, k) ** 0.5
    return lorentz.math.project(b, k=k)


def test_expmap_logmap(a, b, k):
    a = lorentz.math.project(a, k=k)
    b = lorentz.math.project(b, k=k)

    bh = lorentz.math.expmap(x=a, u=lorentz.math.logmap(a, b, k=k), k=k)
    tolerance = {torch.float32: dict(rtol=1e-6, atol=1e-6), torch.float64: dict()}
    np.testing.assert_allclose(bh, b, **tolerance[k.dtype])


def test_parallel_transport_a_b(a, b, k):
    # pointing to the center
    v_0 = torch.rand_like(a)
    u_0 = torch.rand_like(a)

    v_0 = lorentz.math.project_u(a, v_0) # project on tangent plane
    u_0 = lorentz.math.project_u(a, u_0) # project on tangent plane

    v_1 = lorentz.math.parallel_transport(a, b, v_0, k=k)
    u_1 = lorentz.math.parallel_transport(a, b, u_0, k=k)

    # compute norms
    vu_1 = lorentz.math.inner(v_1, u_1, keepdim=True)
    vu_0 = lorentz.math.inner(v_0, u_0, keepdim=True)

    np.testing.assert_allclose(vu_0, vu_1, atol=1e-6, rtol=1e-6)
