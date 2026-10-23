# drift-math

Instalação na raiz do repositório: `python -m pip install -e packages/drift-math`.

Um arquivo por assunto das aulas de Álgebra Linear: `vectors`, `matrices`, `linear_systems`, `vector_spaces`, `subspaces`, `linear_combinations`, `basis`, `transformations`, `trajectory`.

Os vetores são colunas em `np.ndarray` e conjuntos geradores são MATRIZES cujas colunas são vetores. As funções `rref`, `determinant` e `inverse` usam operações elementares explícitas, adequadas ao aprendizado; para sistemas mal-condicionados em uso científico, prefira decomposições de `numpy.linalg`/SciPy.

`vector_spaces.check_axioms_on_examples()` ilustra axiomas numericamente, **não** prova que um conjunto qualquer seja espaço vetorial. `LinearSubspace.kernel(A)` modela o subespaço definido por `Ax=0`, cujo fechamento é um resultado matemático geral. A trajetória coletada não vira um subespaço apenas porque está representada por vetores.

A convenção DIDÁTICA de `transformations` é plano X/Z horizontal, yaw=0 apontando +Z e giro positivo apontando em direção a +X. Esta convenção **não foi validada** no Assetto Corsa, portanto calibração de heading e coordenadas é obrigatória antes de calcular `signed_sideslip_rad`. RPM não é suficiente para calcular trajetória ótima; utilize uma volta gravada como referência até implementar modelo físico.
