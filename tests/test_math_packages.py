import math
import numpy as np
import pytest
from drift_math import vectors, matrices, linear_systems, vector_spaces, subspaces, linear_combinations, basis, transformations, trajectory


def test_vectors_and_angles():
    np.testing.assert_allclose(vectors.add([1,2],[3,4]),[4,6])
    np.testing.assert_allclose(vectors.subtract([4,6],[3,4]),[1,2])
    assert vectors.dot([3,4],[4,-3]) == 0
    assert vectors.norm([3,4]) == 5
    assert vectors.angle_between([1,0],[0,1],degrees=True) == pytest.approx(90)
    assert vectors.signed_angle_2d([1,0],[0,1],degrees=True) == pytest.approx(90)
    np.testing.assert_allclose(vectors.projection([2,4],[1,0]),[2,0])
    with pytest.raises(ValueError): vectors.unit([0,0])


def test_matrices_inverse_det_and_rref_steps():
    a = np.array([[2,1],[1,1]])
    assert matrices.determinant(a) == pytest.approx(1)
    inv = matrices.inverse(a)
    np.testing.assert_allclose(a@inv,np.eye(2))
    assert matrices.rank(a) == 2
    assert matrices.nullity(a) == 0
    result = matrices.rref([[1,2,1],[0,1,2]],record_steps=True)
    np.testing.assert_allclose(result.matrix, [[1,0,-3],[0,1,2]])
    assert len(result.steps) > 0 and result.pivot_columns == (0,1)
    assert matrices.determinant([[1,2],[2,4]]) == 0
    with pytest.raises(ValueError): matrices.inverse([[1,2],[2,4]])


def test_linear_systems_unique_infinite_and_inconsistent():
    out = linear_systems.solve([[1,2],[3,4]],[5,11])
    assert out.kind == "unique"
    np.testing.assert_allclose(out.particular,[1,2])
    infinitely = linear_systems.solve([[1,2],[2,4]],[3,6])
    assert infinitely.kind == "infinite" and infinitely.nullspace_basis.shape == (2,1)
    np.testing.assert_allclose(np.array([[1,2],[2,4]])@infinitely.nullspace_basis,np.zeros((2,1)))
    impossible = linear_systems.solve([[1,2],[2,4]],[3,7])
    assert impossible.kind == "inconsistent" and impossible.particular is None


def test_basis_and_ordered_coordinates():
    generators = [[1,2,0],[0,0,1]]  # 2x3, middle col redundant
    extracted = basis.extract_basis(generators)
    np.testing.assert_allclose(extracted,[[1,0],[0,1]])
    assert basis.dimension_of_span(generators) == 2
    assert not basis.independent(generators)
    coords = basis.coordinates_in_basis([3,4],[[1,1],[0,1]])
    np.testing.assert_allclose(coords,[-1,4])
    change = basis.transition_matrix([[1,0],[0,1]], [[1,1],[0,1]])
    np.testing.assert_allclose(change,[[1,-1],[0,1]])
    extended = basis.extend_basis_to_ambient([[1],[1],[0]])
    assert extended.shape == (3,3) and basis.independent(extended)
    with pytest.raises(ValueError): basis.coordinates_in_basis([1,1],[[1,2],[0,0]])


def test_subspaces_sum_and_intersection():
    u = subspaces.LinearSubspace.generated_by([[1,0],[0,0],[0,0]])
    v = subspaces.LinearSubspace.generated_by([[1,0],[0,1],[0,0]])
    assert u.dimension == 1 and v.dimension == 2
    assert v.contains([1,1,0]) and not u.contains([0,1,0])
    assert u.sum_with(v).dimension == 2
    assert u.intersect(v).dimension == 1
    assert v.intersect(u).dimension == 1
    null = subspaces.LinearSubspace.kernel([[1,0,0],[0,1,0]])
    assert null.dimension == 1 and null.contains([0,0,3])
    empty = subspaces.LinearSubspace.kernel([[1,0],[0,1]])
    assert empty.dimension == 0 and empty.contains([0,0])
    assert not subspaces.affine_constraint_contains([[0,1]],[1],[0,0])


def test_euclidean_axioms_are_examples_not_universal_proof():
    space = vector_spaces.EuclideanSpace(3)
    assert space.contains([1,2,3]) and not space.contains([1,2])
    assert all(vector_spaces.check_axioms_on_examples([[1,2],[3,4],[-5,6]],[2,-3]).values())
    assert space.homogeneous_subspace([[1,0,0]]).dimension == 2


def test_linear_combinations():
    a = [[1,0],[0,1]]
    np.testing.assert_allclose(linear_combinations.combine(a,[2,3]),[2,3])
    assert linear_combinations.is_in_span([4,5],a)
    assert not linear_combinations.is_in_span([1,1],[[1],[0]])
    assert linear_combinations.coefficients_for([4,5],a).kind == "unique"


def test_transformations_and_sideslip():
    rot = transformations.rotation_2d(math.pi/2)
    np.testing.assert_allclose(rot@[1,0],[0,1],atol=1e-12)
    local = transformations.xz_world_to_vehicle([3,1,4],0)
    np.testing.assert_allclose(local,[3,4])
    world = transformations.xz_vehicle_to_world(local,0,vertical_mps=1)
    np.testing.assert_allclose(world,[3,1,4])
    yaw = 0.6
    np.testing.assert_allclose(transformations.xz_world_to_vehicle(
        transformations.xz_vehicle_to_world([5,12],yaw), yaw),[5,12])
    assert trajectory.signed_sideslip_rad([0,0,0],0) is None
    assert math.degrees(trajectory.signed_sideslip_rad([10,0,10],0)) == pytest.approx(45)


def test_trajectory_sampling_and_geometry():
    pts = [[0,0],[10,0],[10,10]]
    resampled = trajectory.resample_by_distance(pts,5)
    np.testing.assert_allclose(resampled,[[0,0],[5,0],[10,0],[10,5],[10,10]])
    closest = trajectory.closest_on_polyline([8,2],[[0,0],[10,0]])
    assert closest.distance_m == pytest.approx(2)
    assert closest.position_xz_m == pytest.approx((8,0))
    assert closest.signed_offset_m > 0
    assert trajectory.cumulative_length(pts)[-1] == pytest.approx(20)
    np.testing.assert_allclose(trajectory.xz_path([[1,4,2],[3,5,6]]),[[1,2],[3,6]])
