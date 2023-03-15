from paddleocr import PaddleOCR
from pond import PooledObjectFactory, PooledObject, Pond


class MyOcr(PaddleOCR):
    name: str
    validate_result: bool = True

    def __init__(self):
        super().__init__(use_angle_cls=True, lang="ch")


class PooledOcrFactory(PooledObjectFactory):
    def creatInstantce(self) -> PooledObject:
        ocr = MyOcr()
        ocr.name = "myocr"
        return PooledObject(ocr)

    def destroy(self, pooled_object: PooledObject):
        del pooled_object

    def reset(self, pooled_object: PooledObject) -> PooledObject:
        pooled_object.keeped_object.name = "myocr"
        return pooled_object

    def validate(self, pooled_object: PooledObject) -> bool:
        return pooled_object.keeped_object.validate_result


# borrowed_timeout ：单位为秒，借出对象的最长期限，超过期限的对象归还时会自动销毁不会放入对象池。
# time_between_eviction_runs ：单位为秒，自动回收的间隔时间。
# thread_daemon ：守护线程，如果为 True，自动回收的线程会随着主线程关闭而关闭。
# eviction_weight ：自动回收时权重，会将这个权重与最大使用频次想乘，使用频次小于这个值的对象池中的对象都会进入清理步骤。
pond = Pond(borrowed_timeout=2,
            time_between_eviction_runs=-1,
            thread_daemon=True,
            eviction_weight=0.8)

# pooled_maxsize: 对象池的最大能放置的数量
# least_one: 如果为 True，在进入自动清理时，这个工厂类生成出的对象的对象池会至少保留一个对象
ocr_factory = PooledOcrFactory(pooled_maxsize=8, least_one=False)

# 向 Pond 注册这个工厂对象，默认会使用 factory 的类名作为 PooledObjectTree 的 key
pond.register(ocr_factory)

# 利用方式： 参考 https://www.qin.news/pond/
