from types import SimpleNamespace

from learning.services import compare_answer, generate_exercise, numeric_rank2


s1 = SimpleNamespace(
    sequence=1, position_world_m=[10.0, 0.0, 5.0], velocity_world_mps=[3.0, 0.0, 4.0],
)
s2 = SimpleNamespace(
    sequence=2, position_world_m=[14.0, 0.0, 8.0], velocity_world_mps=[5.0, 0.0, 6.0],
)


def test_displacement_and_hidden_solution():
    exercise = generate_exercise("displacement", s1, s2)
    assert exercise["expected_result"] == {
        "delta_x_m": 4.0, "delta_z_m": 3.0, "distance_horizontal_m": 5.0,
    }
    assert "solution" not in exercise
    assert len(generate_exercise("displacement", s1, s2, reveal=True)["solution"]) >= 2


def test_combination_and_subspace():
    exercise = generate_exercise("combination", s1, s2)
    assert exercise["expected_result"] == {"a": 4.0, "b": 3.0}
    subspace = generate_exercise("subspace", s1, s2)
    assert subspace["expected_result"] == {"is_subspace": True, "dimension": 1}
    assert subspace["calculation"]["direction_vector"] == [3.0, 4.0]
    assert subspace["calculation"]["norm"] == 5.0
    assert subspace["calculation"]["multiples"][1] == {"t": 0, "vector": [0.0, 0.0]}
    assert subspace["calculation"]["basis"] == [[3.0, 4.0]]
    basis = generate_exercise("basis_dimension", s1, s2)
    assert basis["calculation"]["sample_sequences"] == [1, 2]
    assert basis["calculation"]["matrix"] == [[3.0, 4.0], [5.0, 6.0]]
    assert basis["calculation"]["determinant"] == -2.0
    assert basis["calculation"]["dimension"] == 2


def test_determinant_inverse_gauss_and_rank():
    assert generate_exercise("determinant", s1, s2)["expected_result"] == -2.0
    assert generate_exercise("gauss", s1, s2)["expected_result"] == [2.0, -1.0]
    matrix_inverse = generate_exercise("inverse", s1, s2)["expected_result"]
    assert matrix_inverse == [[-3.0, 2.0], [2.5, -1.5]]
    assert numeric_rank2((1.0, 2.0), (2.0, 4.0)) == 1
    assert numeric_rank2((1.0, 0.0), (0.0, 1.0)) == 2


def test_answer_comparison():
    assert compare_answer({"a": 4.0}, {"a": 4.01})
    assert not compare_answer({"a": 4.0}, {"a": 8.0})
    assert compare_answer([2.0, -1.0], [2.0, -1.0])
    assert not compare_answer(True, 1)


def test_affine_subspace_as_counterexample():
    exercise = generate_exercise("affine_subspace", s1, s2, reveal=True)
    assert exercise["expected_result"] == {"is_subspace": False, "dimension": None}
    assert any("zero" in line for line in exercise["solution"])
