from typing import List, Union
import logging
import pkgutil
from OpenGL import GL
from gltfio.types import *
from gltfio.parser import GltfData
import glglue.gl3.vbo
from glglue import ctypesmath
from glglue.scene.texture import Image32, Texture
from glglue.scene.material import Material
from glglue.scene.mesh import Mesh
from glglue.scene.node import Node
from glglue.scene.vertices import VectorView, Planar
from .animation import Animation

logger = logging.getLogger(__name__)


def get_shader(name: str) -> str:
    data = pkgutil.get_data('gltfloupe', f'assets/{name}')
    if not data:
        raise Exception()
    return data.decode('utf-8')


VS = get_shader('gltf.vs')
FS = get_shader('gltf.fs')


MAP = {
    'B': ctypes.c_uint8,
    'H': ctypes.c_uint16,
    'I': ctypes.c_uint32,
    'L': ctypes.c_uint32,
    'f': ctypes.c_float,
}


def get_vectorview(src: GltfAccessorSlice) -> VectorView:
    return VectorView(src.scalar_view, MAP[src.scalar_view.format], src.element_count)


def get_transform(gltf_node: GltfNode) -> Union[ctypesmath.Mat4, ctypesmath.TRS]:
    if gltf_node.matrix:
        return ctypesmath.Mat4(*gltf_node.matrix)

    t = ctypesmath.Float3(0, 0, 0)
    if gltf_node.translation:
        t = ctypesmath.Float3(*gltf_node.translation)

    r = ctypesmath.Quaternion(0, 0, 0, 1)
    if gltf_node.rotation:
        r = ctypesmath.Quaternion(*gltf_node.rotation)

    s = ctypesmath.Float3(1, 1, 1)
    if gltf_node.scale:
        s = ctypesmath.Float3(*gltf_node.scale)

    return ctypesmath.TRS(t, r, s)


class GltfLoader:
    def __init__(self, gltf: GltfData) -> None:
        self.gltf = gltf
        # Corresponds to the index of GltfData
        self.images: List[Image32] = []
        self.textures: List[Texture] = []
        self.materials: List[Material] = []
        self.meshes: List[List[Mesh]] = []
        self.nodes: List[Node] = []
        self.root: Optional[Node] = None
        # animation
        self.animations: List[Animation] = []
        self.time = 0.0

    def _load_image(self, src: GltfImage):
        image = Image32.load(src.data)
        self.images.append(image)

    def _load_texture(self, src: GltfTexture):
        texture = Texture(src.name, self.images[src.image.index])
        self.textures.append(texture)

    def _load_material(self, src: GltfMaterial):
        material = Material(src.name, VS, FS)
        if src.base_color_texture:
            material.color_texture = self.textures[src.base_color_texture.index]
        self.materials.append(material)

    def _load_mesh(self, name: str, src: GltfPrimitive):
        macro = ['#version 330']
        attributes: List[glglue.gl3.vbo.VectorView] = [
            get_vectorview(src.position)]
        # if prim.normal:
        #     attributes.append(glglue.gl3.vbo.TypedBytes(*prim.normal))
        #     macro += f'#define HAS_NORMAL 1\n'
        if src.uv0:
            attributes.append(get_vectorview(src.uv0))
            macro.append('#define HAS_UV 1')
        indices = None
        if src.indices:
            indices = get_vectorview(src.indices)

        mesh = Mesh(name, Planar(attributes), indices)
        mesh.aabb = ctypesmath.AABB(ctypesmath.Float3(
            *src.position_min), ctypesmath.Float3(*src.position_max))
        mesh.add_submesh(
            self.materials[src.material.index], macro, GL.GL_TRIANGLES)
        self.meshes[-1].append(mesh)

    def _load_node(self, src: GltfNode):
        t = get_transform(src)
        node = Node(src.name, t)
        self.nodes.append(node)
        if src.mesh:
            for i, _ in enumerate(src.mesh.primitives):
                mesh = self.meshes[src.mesh.index][i]
                node.meshes.append(mesh)

    def _build_node_hierarchy(self, src: List[GltfNode], dst: Node):
        for gltf_node in src:
            node = self.nodes[gltf_node.index]
            dst.children.append(node)
            self._build_node_hierarchy(gltf_node.children, node)

    def _load_animation(self, src: GltfAnimation):
        animation = Animation.from_gltf(src, self.nodes)
        self.animations.append(animation)

    def load(self) -> Node:
        for image in self.gltf.images:
            self._load_image(image)
        for texture in self.gltf.textures:
            self._load_texture(texture)
        for material in self.gltf.materials:
            self._load_material(material)
        for mesh in self.gltf.meshes:
            self.meshes.append([])
            for i, prim in enumerate(mesh.primitives):
                self._load_mesh(f'{mesh.name}:{i}', prim)
        for node in self.gltf.nodes:
            self._load_node(node)
        for animation in self.gltf.animations:
            self._load_animation(animation)

        # root
        self.root = Node('__scene__', ctypesmath.Mat4.new_identity())
        self._build_node_hierarchy(self.gltf.scene, self.root)
        return self.root

    def set_time(self, time: float):
        if self.time == time:
            return

        for animation in self.animations:
            animation.set_time(time)

        if self.root:
            self.root.calc_world()

        # update CPU skinning
        for node in self.nodes:
            if node.meshes:
                pass
