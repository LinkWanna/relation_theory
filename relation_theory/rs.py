from itertools import combinations

from .fd import FD, FDSet


class RelationSchema:
    """表示关系模式 R 和其函数依赖集 F"""

    def __init__(self, attributes: set[str], fd_set: FDSet):
        self.attributes = frozenset(attributes)
        self.fd_set: FDSet = fd_set

    def candidate_keys(self) -> list[set[str]]:
        """
        求关系模式的所有候选码（在所有属性中，能唯一标识元组的最小属性集）

        属性集 K 是候选码，当且仅当：
        1. K 的闭包包含所有属性（K+ = R）
        2. K 的任何真子集的闭包不包含所有属性（即 K 是最小的）
        """
        U = self.attributes
        fds = self.fd_set

        # 1. 分类属性
        all_left = set()
        all_right = set()
        for fd in fds.fds:
            all_left.update(fd.lhs)
            all_right.update(fd.rhs)

        left = all_left - all_right  # 仅在左侧出现的属性
        # right = all_right - all_left  # 仅在右侧出现的属性（不需要）
        both = all_left & all_right  # 在左右两侧都出现的属性
        isolated = U - (all_left | all_right)  # 孤立属性

        # 2. 枚举 both 的子集
        candidates = []
        for r in range(len(both) + 1):
            for subset in combinations(both, r):
                candidate = set(left) | set(subset) | set(isolated)
                closure_set = fds.closure(candidate)

                # 检查是否为超码
                if closure_set == U:
                    # 检查最小性
                    is_minimal = True
                    for attr in candidate:  # 检查 candidate 的每个属性是否可去除
                        test_set = candidate - {attr}
                        if fds.closure(test_set) == U:
                            is_minimal = False
                            break
                    if is_minimal:
                        candidates.append(candidate)

        return candidates

    def _judge_2NF(self, candidate_keys: list[set]) -> list[str]:
        """
        关系模式满足 2NF
        <=> 每一个非主属性都完全函数依赖于每一个候选码
        <=> 对任意函数依赖 X→A∈F+（或由 F 逻辑蕴含），
            若 A 是非主属性，且存在候选码 K∈K 使得 X⊆K，
            则必有 X=K（即 A 不部分依赖于 K）。
        """
        # 计算主属性集
        prime_attrs = set()
        for key in candidate_keys:
            prime_attrs.update(key)

        # 检查每个 FD 是否违反 2NF
        atomic_fds = self.fd_set.singleton_rhs().fds
        violations = []
        for fd in atomic_fds:
            for key in candidate_keys:
                # 存在部分函数依赖需要满足两个条件：
                # 1. fd.lhs 是候选码的真子集
                # 2. fd.rhs 不包含主属性
                if fd.lhs < key and not fd.rhs <= prime_attrs:
                    # 存在部分依赖，违反 2NF
                    violations.append(
                        f"Violation: {''.join(sorted(fd.lhs))} -> {''.join(sorted(fd.rhs))} "
                        f"is a partial dependency on candidate key {''.join(sorted(key))}"
                    )
                    break  # 对该 fd 找到一个候选码即可

        return violations  # 不存在部分依赖，满足 2NF

    def _judge_3NF(self, candidate_keys: list[set]) -> list[str]:
        """
        关系模式满足 3NF
        <=> 不存在非主属性对候选码的传递函数依赖
        <=> 不存在非候选码对非主属性的函数依赖
        <=> 对任意函数依赖 X→A∈F+（或由 F 逻辑蕴含），
            必有 X 是超码，或 A 是主属性。
        """

        prime_attrs = set()
        for key in candidate_keys:
            prime_attrs.update(key)

        # 检查每个 FD 是否违反 3NF
        violations = []
        atomic_fds = self.fd_set.singleton_rhs().fds
        for fd in atomic_fds:
            # 存在传递依赖需要满足两个条件：
            # 1. fd.lhs 不是超码（即不包含任何候选码）
            # 2. fd.rhs 包含非主属性
            if all(not fd.lhs >= key for key in candidate_keys) and not fd.rhs <= prime_attrs:
                # 存在传递依赖，违反 3NF
                violations.append(f"Violation: {''.join(sorted(fd.lhs))} -> {''.join(sorted(fd.rhs))} is a transitive dependency")

        return violations  # 不存在传递依赖，满足 3NF

    def _judge_BCNF(self, candidate_keys: list[set]) -> list[str]:
        """
        关系模式满足 BCNF
        <=> 对任意函数依赖 X→A∈F+（或由 F 逻辑蕴含），必有 X 是超码。
        """

        # 检查每个 FD 是否违反 BCNF
        violations = []
        atomic_fds = self.fd_set.singleton_rhs().fds
        for fd in atomic_fds:
            # 存在违反 BCNF 需要满足：
            # fd.lhs 不是超码（即不包含任何候选码）
            if all(not fd.lhs >= key for key in candidate_keys):
                # 存在违反 BCNF 的 FD
                violations.append(f"Violation: {''.join(sorted(fd.lhs))} -> {''.join(sorted(fd.rhs))} violates BCNF")

        return violations

    def judge_NF(self) -> tuple[str, list[str]]:
        """判断关系模式满足的范式等级"""
        candidate_keys = self.candidate_keys()

        violations_2NF = self._judge_2NF(candidate_keys)
        if violations_2NF:
            return ("1NF", violations_2NF)

        violations_3NF = self._judge_3NF(candidate_keys)
        if violations_3NF:
            return ("2NF", violations_3NF)

        violations_BCNF = self._judge_BCNF(candidate_keys)
        if violations_BCNF:
            return ("3NF", violations_BCNF)

        return ("BCNF", [])

    def is_lossless_decomposition(self, sub_schemas: list[set[str]]) -> bool:
        """
        分解为无损分解
        <=> 如果 ∃Ri​∈ρ，使得 Ri​ 是原关系 R 的超码（即 Ri+​=U），则分解 ρ 是无损的。
        """
        # 1. 求候选码
        candidate_keys = self.candidate_keys()

        # 2. 检查每个子模式是否包含候选码
        for sub_schema in sub_schemas:
            if any(key <= sub_schema for key in candidate_keys):
                return True  # 存在子模式包含候选码，分解无损

        return False

    @classmethod
    def from_str(cls, attributes: str, fd_list: list[str]) -> "RelationSchema":
        """便捷构造：R('ABCD', ['A->B', 'BC->D'])"""
        attr_set = set(attributes)
        fds = []

        for fd_str in fd_list:
            if "->" not in fd_str:
                raise ValueError(f"Invalid FD format (missing '->'): '{fd_str}'")
            lhs, rhs = fd_str.split("->", 1)
            lhs = frozenset(lhs.strip())
            rhs = frozenset(rhs.strip())

            if not lhs:
                raise ValueError(f"Empty left-hand side in FD: '{fd_str}'")
            fds.append(FD(lhs, rhs))

        return cls(attr_set, FDSet(fds))

    def __repr__(self):
        return f"R({''.join(sorted(self.attributes))}), F = {{{', '.join(map(str, self.fd_set.fds))}}}"
