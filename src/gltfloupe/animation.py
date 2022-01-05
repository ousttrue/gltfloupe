from typing import List
import ctypes
from glglue.scene.node import Node
from gltfio.parser import GltfAnimation, GltfAnimationTargetPath, GltfAnimationInterpolation


def lerp(low: float, hight: float, ratio: float) -> float:
    return low + (hight-low) * ratio


class Curve:
    def __init__(self, node: Node, element_count: int, count: int) -> None:
        self.node = node
        self.element_count = element_count
        self.times = (ctypes.c_float * count)()
        self.values = (ctypes.c_float * (element_count * count))()

    def __str__(self) -> str:
        return f'{self.node.name}.{self.target}: {self.times[-1]} sec'

    @property
    def target(self) -> str:
        raise NotImplementedError()

    def set_key(self, pos: int, time: float, value: tuple):
        self.times[pos] = time
        i = pos * self.element_count
        for v in value:
            self.values[i]
            i += 1

    def get_value(self, index: int) -> List[float]:
        begin = self.element_count * index
        return self.values[begin:begin+self.element_count]

    def set_time(self, time: float):
        first = self.times[0]
        end = self.times[-1]
        if time <= self.times[0]:
            self.apply(self.get_value(0))
        elif time >= self.times[-1]:
            self.apply(self.get_value(-1))
        else:
            for i, (l, r) in enumerate(zip(self.times[:-1], self.times[1:])):
                ll = self.get_value(i)
                rr = self.get_value(i+1)
                if l == time:
                    self.apply(ll)
                elif r == time:
                    self.apply(rr)
                else:
                    # LINEAR
                    ratio = (time-l)/(r-l)
                    self.apply_lerp(ll, rr, ratio)

    def apply(self, value: List[float]):
        # implement inherited class
        raise NotImplementedError()

    def apply_lerp(self, low, high, ratio):
        raise NotImplementedError()


class TranslationCurve(Curve):
    def __init__(self, node: Node, count: int) -> None:
        super().__init__(node, 3, count)

    @property
    def target(self) -> str:
        return 'target'

    def apply(self, value: List[float]):
        assert len(value) == 3
        self.node.local_transform.trnslation.x = value[0]
        self.node.local_transform.trnslation.y = value[1]
        self.node.local_transform.trnslation.z = value[2]

    def apply_lerp(self, low, high, ratio):
        assert len(low) == 3
        assert len(high) == 3
        self.node.local_transform.trnslation.x = lerp(low[0], high[0], ratio)
        self.node.local_transform.trnslation.y = lerp(low[1], high[1], ratio)
        self.node.local_transform.trnslation.z = lerp(low[2], high[2], ratio)


class RotationCurve(Curve):
    def __init__(self, node: Node, count: int) -> None:
        super().__init__(node, 4, count)

    @property
    def target(self) -> str:
        return 'rotation'

    def apply(self, value: List[float]):
        assert len(value) == 4
        self.node.local_transform.rotation.x = value[0]
        self.node.local_transform.rotation.y = value[1]
        self.node.local_transform.rotation.z = value[2]
        self.node.local_transform.rotation.w = value[3]

    def apply_lerp(self, low, high, ratio):
        # TODO: slerp
        assert len(low) == 4
        assert len(high) == 4
        self.node.local_transform.rotation.x = lerp(low[0], high[0], ratio)
        self.node.local_transform.rotation.y = lerp(low[1], high[1], ratio)
        self.node.local_transform.rotation.z = lerp(low[2], high[2], ratio)
        self.node.local_transform.rotation.z = lerp(low[3], high[3], ratio)


class ScaleCurve(Curve):
    def __init__(self, node: Node, count: int) -> None:
        super().__init__(node, 3, count)

    @property
    def target(self) -> str:
        return 'scale'

    def apply(self, value: List[float]):
        assert len(value) == 3
        self.node.local_transform.scale.x = value[0]
        self.node.local_transform.scale.y = value[1]
        self.node.local_transform.scale.z = value[2]

    def apply_lerp(self, low, high, ratio):
        assert len(low) == 3
        assert len(high) == 3
        self.node.local_transform.scale.x = lerp(low[0], high[0], ratio)
        self.node.local_transform.scale.y = lerp(low[1], high[1], ratio)
        self.node.local_transform.scale.z = lerp(low[2], high[2], ratio)


class WeightCurve(Curve):
    def __init__(self, node: Node, count: int) -> None:
        super().__init__(node, 1, count)

    @property
    def target(self) -> str:
        return 'weight'

    def apply(self, value: List[float]):
        assert len(value) == 1
        # TODO:

    def apply_lerp(self, low, high, ratio):
        assert len(low) == 1
        assert len(high) == 1
        # TODO:


class Animation:
    def __init__(self, name: str) -> None:
        self.name = name
        self.curves: List[Curve] = []
        self.last_time = 0

    def add_curve(self, curve: Curve):
        self.curves.append(curve)

        curve_time = curve.times[-1]
        if curve_time > self.last_time:
            self.last_time = curve_time

    def set_time(self, time: float):
        for curve in self.curves:
            curve.set_time(time)

    @staticmethod
    def from_gltf(src: GltfAnimation, nodes: List[Node]) -> 'Animation':
        animation = Animation(src.name)
        for ch in src.channels:
            node = ch.target.node_index
            curve = None
            sampler = src.samplers[ch.sampler]
            match ch.target.path:
                case GltfAnimationTargetPath.Translation:
                    curve = TranslationCurve(
                        nodes[node.index], sampler.input.get_count())
                    animation.add_curve(curve)
                case GltfAnimationTargetPath.Rotation:
                    curve = RotationCurve(
                        nodes[node.index], sampler.input.get_count())
                    animation.add_curve(curve)
                case GltfAnimationTargetPath.Scale:
                    curve = ScaleCurve(
                        nodes[node.index], sampler.input.get_count())
                    animation.add_curve(curve)
                case GltfAnimationTargetPath.Weights:
                    curve = WeightCurve(
                        nodes[node.index], sampler.input.get_count())
                    animation.add_curve(curve)
                case _:
                    raise NotImplementedError()

            match sampler.interpolation:
                case GltfAnimationInterpolation.Linear:
                    for i, (time, value) in enumerate(zip(sampler.input, sampler.output)):
                        # time: (ctypes.c_float * 1)
                        # value: (ctypes.c_float * N)
                        curve.set_key(i, time[0], value)  # type: ignore
                case _:
                    raise NotImplementedError()
            animation.add_curve(curve)
            # logger.debug(f'{curve}')
        return animation
