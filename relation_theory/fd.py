class FD:
    """表示一个函数依赖（FunctionalDependency） A -> B"""

    def __init__(self, lhs: frozenset[str] | set[str], rhs: frozenset[str] | set[str]):
        """lhs: 左侧属性集，rhs: 右侧属性集"""
        self.lhs = frozenset(lhs)
        self.rhs = frozenset(rhs)

    def __eq__(self, other):
        return isinstance(other, FD) and self.lhs == other.lhs and self.rhs == other.rhs

    def __hash__(self):
        return hash((self.lhs, self.rhs))

    def __repr__(self):
        return f"{''.join(sorted(self.lhs))} → {''.join(sorted(self.rhs))}"


class FDSet:
    """表示一组函数依赖集，例如，FDSet({A -> B, B -> C})"""

    def __init__(self, fds: list[FD] = []):
        self.fds: list[FD] = fds

    def implies(self, fd: FD) -> bool:
        """判断当前 FDSet 是否能推出 fd"""
        return fd.rhs.issubset(self.closure(fd.lhs))

    def closure(self, attributes) -> set[str]:
        """计算属性集关于 FDSet 的闭包"""
        closure_set = set(attributes)
        changed = True
        while changed:
            changed = False
            for fd in self.fds:
                if fd.lhs.issubset(closure_set) and not fd.rhs.issubset(closure_set):
                    closure_set.update(fd.rhs)
                    changed = True
        return closure_set

    def singleton_rhs(self) -> "FDSet":
        """将所有函数依赖的右侧属性集拆分为单一属性"""
        singleton_fds = []
        for fd in self.fds:
            for attr in fd.rhs:
                singleton_fds.append(FD(fd.lhs, frozenset(attr)))
        return FDSet(singleton_fds)

    def canonical_cover(self) -> "FDSet":
        """计算最小函数依赖集（最小覆盖）"""
        # Step 1: Right-hand side singleton
        singleton_fds = self.singleton_rhs().fds

        # Step 2: Minimize left-hand sides
        minimized_fds = []
        for fd in singleton_fds:
            minimal_lhs = set(fd.lhs)
            rhs_attr = next(iter(fd.rhs))  # 安全获取唯一 RHS 属性
            for attr in list(fd.lhs):  # 遍历原始 lhs 的副本
                candidate = minimal_lhs - {attr}
                # 构造临时 FDSet 来计算闭包（注意：这里应使用当前所有 singleton_fds）
                if rhs_attr in FDSet(singleton_fds).closure(candidate):
                    minimal_lhs.discard(attr)
            minimized_fds.append(FD(frozenset(minimal_lhs), frozenset(rhs_attr)))  # 保持 rhs 为单元素集合

        # Remove duplicates (requires __hash__ or use manual dedup)
        # Since FD is not hashable by default, we dedup manually
        unique_fds = []
        for fd in minimized_fds:
            if fd not in unique_fds:
                unique_fds.append(fd)

        # Step 3: Iteratively remove redundant dependencies
        changed = True
        while changed:
            changed = False
            i = 0
            while i < len(unique_fds):
                fd = unique_fds[i]
                others = FDSet(unique_fds[:i] + unique_fds[i + 1 :])
                if others.implies(fd):
                    unique_fds.pop(i)
                    changed = True
                else:
                    i += 1

        return FDSet(unique_fds)

    def __eq__(self, other):
        """判断两个 FDSet 是否等价：相互蕴含"""
        for fd in self.fds:
            if not other.implies(fd):
                return False
        for fd in other.fds:
            if not self.implies(fd):
                return False
        return True

    def __repr__(self):
        return "{" + ", ".join(repr(fd) for fd in sorted(self.fds, key=lambda x: (sorted(x.lhs), sorted(x.rhs)))) + "}"
