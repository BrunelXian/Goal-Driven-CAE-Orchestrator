# Test Fixture Policy

1. 所有 fixture 默认是 synthetic 或 test-only。
2. fixture 不是 Abaqus execution evidence。
3. fixture 不是 ODB validity evidence。
4. fixture 不是 physical evidence。
5. mock PASS 不能被解释为 Runtime production PASS。
6. physical evidence eligible 默认值必须是 `NO`。
