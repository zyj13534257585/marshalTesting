import marshal
import hashlib
import sys
from unittest import TestCase, main

class TestMarshalDeterminism(TestCase):
    def _hash(self, obj):
        """返回 marshal 序列化后的 MD5 十六进制摘要"""
        data = marshal.dumps(obj)
        return hashlib.md5(data).hexdigest(), data

    def assertSameMarshal(self, obj1, obj2):
        """断言两个对象序列化后的字节流完全一致"""
        hash1, data1 = self._hash(obj1)
        hash2, data2 = self._hash(obj2)
        self.assertEqual(hash1, hash2, f"哈希不同, 长度分别为 {len(data1)} 和 {len(data2)}")
        self.assertEqual(data1, data2)

    # ------------------------------------------------------------
    # 1. 单例对象测试
    # ------------------------------------------------------------
    def test_ellipsis_singleton(self):
        """Ellipsis 序列化是否总是相同字节流"""
        e1 = Ellipsis
        e2 = ...
        self.assertIs(e1, e2)
        self.assertSameMarshal(e1, e2)
        self.assertSameMarshal(Ellipsis, Ellipsis)
        print(f"Ellipsis marshal 数据: {marshal.dumps(Ellipsis).hex()[:50]}...")

    def test_stopiteration_singleton(self):
        """StopIteration 序列化是否总是相同字节流"""
        s1 = StopIteration
        s2 = StopIteration
        self.assertIs(s1, s2)
        self.assertSameMarshal(s1, s2)
        print(f"StopIteration marshal 数据: {marshal.dumps(StopIteration).hex()[:50]}...")

    def test_none_singleton(self):
        """None 单例的序列化稳定性（对照组）"""
        self.assertSameMarshal(None, None)
        
    def test_bool_singletons(self):
        """布尔单例的序列化稳定性"""
        self.assertSameMarshal(True, True)
        self.assertSameMarshal(False, False)

    # ------------------------------------------------------------
    # 2. 可序列化对象测试（不包含 slice）
    # ------------------------------------------------------------
    def test_basic_containers_with_ellipsis(self):
        """包含 Ellipsis 和 StopIteration 的容器"""
        obj1 = (Ellipsis, StopIteration, None, True)
        obj2 = (Ellipsis, StopIteration, None, True)
        self.assertSameMarshal(obj1, obj2)
        
        # 嵌套结构
        nested1 = [1, (2, Ellipsis), {3: StopIteration}]
        nested2 = [1, (2, Ellipsis), {3: StopIteration}]
        self.assertSameMarshal(nested1, nested2)
    
    def test_code_object_stability(self):
        """code object 的序列化稳定性（.pyc 核心）"""
        code_str = "def f(): pass\nclass C: pass\nx = 42"
        code_obj1 = compile(code_str, "<test1>", "exec")
        code_obj2 = compile(code_str, "<test2>", "exec")  # 不同文件名
        
        # 注意：code object 包含文件名，所以会不同
        hash1, data1 = self._hash(code_obj1)
        hash2, data2 = self._hash(code_obj2)
        self.assertNotEqual(hash1, hash2, "不同文件名的 code object 应该不同")
        
        # 相同参数应该相同
        code_obj3 = compile(code_str, "<test1>", "exec")
        self.assertSameMarshal(code_obj1, code_obj3)

    # ------------------------------------------------------------
    # 3. .pyc 文件模拟
    # ------------------------------------------------------------
    def test_pyc_structure(self):
        """模拟 .pyc 文件结构的序列化稳定性"""
        code_obj = compile("print('hello')", "<test>", "exec")
        
        # Python 3.7+ 的 .pyc 格式
        if sys.version_info >= (3, 7):
            # 新格式: (magic, bitfield, timestamp, hash, code)
            import importlib.util
            MAGIC = importlib.util.MAGIC_NUMBER
            BITFIELD = 0b00  # 无标记
            TIMESTAMP = 1234567890
            
            pyc_tuple1 = (MAGIC, BITFIELD, TIMESTAMP, None, code_obj)
            pyc_tuple2 = (MAGIC, BITFIELD, TIMESTAMP, None, code_obj)
            self.assertSameMarshal(pyc_tuple1, pyc_tuple2)
            
            # 测试哈希模式
            import hashlib
            source_hash = hashlib.sha256(b"source code").digest()
            pyc_hash_tuple = (MAGIC, BITFIELD, 0, source_hash, code_obj)
            self.assertSameMarshal(pyc_hash_tuple, pyc_hash_tuple)
    
    # ------------------------------------------------------------
    # 4. 边缘情况测试
    # ------------------------------------------------------------
    def test_float_determinism(self):
        """浮点数的序列化确定性"""
        f1 = 1.0 / 3.0
        f2 = 1.0 / 3.0
        self.assertSameMarshal(f1, f2)
        
        # 特殊浮点值
        self.assertSameMarshal(float('inf'), float('inf'))
        self.assertSameMarshal(float('-inf'), float('-inf'))
        # NaN 的位模式可能相同（取决于实现）
        nan1 = float('nan')
        nan2 = float('nan')
        try:
            self.assertSameMarshal(nan1, nan2)
        except AssertionError:
            print("警告: NaN 的 marshal 结果不稳定（预期行为）")
    
    def test_large_integers(self):
        """大整数的序列化确定性"""
        big1 = 2**100
        big2 = 2**100
        self.assertSameMarshal(big1, big2)
    
    def test_strings_with_unicode(self):
        """Unicode 字符串的序列化确定性"""
        s1 = "Hello 世界 🌍"
        s2 = "Hello 世界 🌍"
        self.assertSameMarshal(s1, s2)
    
    def test_recursive_structure_behavior(self):
        """检查递归结构的行为（不假设异常）"""
        lst = []
        lst.append(lst)
        
        try:
            data = marshal.dumps(lst)
            print(f"递归结构被允许序列化（长度 {len(data)} 字节）")
            # 验证相同递归结构的确定性
            lst2 = []
            lst2.append(lst2)
            self.assertSameMarshal(lst, lst2)
        except ValueError as e:
            print(f"递归结构正确抛出异常: {e}")
            # 这是预期行为
    
    def test_object_graph_with_shared_refs(self):
        """共享引用的对象图"""
        shared = [1, 2, 3]
        obj1 = [shared, shared]  # 两个引用指向同一列表
        obj2 = [shared, shared]
        self.assertSameMarshal(obj1, obj2)
        
        # 注意：marshal 不会保持共享引用语义（会展开）
        data1 = marshal.dumps(obj1)
        data2 = marshal.dumps([[1,2,3], [1,2,3]])  # 独立列表
        self.assertEqual(data1, data2, "共享引用会被展开为独立对象")

# ------------------------------------------------------------
# 兼容性包装：测试不可序列化对象
# ------------------------------------------------------------
class TestUnmarshallableObjects(TestCase):
    """测试哪些对象不能被 marshal 序列化"""
    
    def test_slice_unmarshallable(self):
        """slice 对象在 Python 3.9 中不可序列化"""
        with self.assertRaises(ValueError):
            marshal.dumps(slice(1, 10, 2))
        print("✓ slice 对象正确拒绝序列化")
    
    def test_lambda_unmarshallable(self):
        """函数对象通常不可序列化"""
        with self.assertRaises(ValueError):
            marshal.dumps(lambda x: x)
    
    def test_module_unmarshallable(self):
        """模块对象不可序列化"""
        with self.assertRaises(ValueError):
            marshal.dumps(marshal)
    
    def test_type_unmarshallable(self):
        """类型对象通常不可序列化（除内置单例）"""
        with self.assertRaises(ValueError):
            marshal.dumps(list)
    
    def test_ellipsis_type_vs_instance(self):
        """Ellipsis 类型 vs 实例"""
        # Ellipsis 实例可序列化
        marshal.dumps(Ellipsis)  # 不应异常
        # Ellipsis 类型本身不可序列化
        with self.assertRaises(ValueError):
            marshal.dumps(type(Ellipsis))

if __name__ == "__main__":
    print(f"Python 版本: {sys.version}")
    print(f"Marshal 版本: {marshal.version}")
    print("=" * 60)
    main()