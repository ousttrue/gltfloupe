import ctypes
import logging
import contextlib
from OpenGL import GL
import cydeer as imgui

logger = logging.getLogger(__name__)


VERTEX_SHADER_SRC = """
#version 330

uniform mat4 ProjMtx;
in vec2 Position;
in vec2 UV;
in vec4 Color;
out vec2 Frag_UV;
out vec4 Frag_Color;

void main() {
    Frag_UV = UV;
    Frag_Color = Color;

    gl_Position = ProjMtx * vec4(Position.xy, 0, 1);
}
"""

FRAGMENT_SHADER_SRC = """
#version 330

uniform sampler2D Texture;
in vec2 Frag_UV;
in vec4 Frag_Color;
out vec4 Out_Color;

void main() {
    Out_Color = Frag_Color * texture(Texture, Frag_UV.st);
}
"""


@contextlib.contextmanager
def save_texture():
    last_texture = GL.glGetIntegerv(GL.GL_TEXTURE_BINDING_2D)
    try:
        yield
    finally:
        GL.glBindTexture(GL.GL_TEXTURE_2D, last_texture)


@contextlib.contextmanager
def save_state():
    # save state
    last_texture = GL.glGetIntegerv(GL.GL_TEXTURE_BINDING_2D)
    last_array_buffer = GL.glGetIntegerv(GL.GL_ARRAY_BUFFER_BINDING)
    last_vertex_array = GL.glGetIntegerv(GL.GL_VERTEX_ARRAY_BINDING)
    try:
        yield
    finally:
        # restore state
        GL.glBindTexture(GL.GL_TEXTURE_2D, last_texture)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, last_array_buffer)
        GL.glBindVertexArray(last_vertex_array)


@contextlib.contextmanager
def save_render_state():
    last_program = GL.glGetIntegerv(GL.GL_CURRENT_PROGRAM)
    last_texture = GL.glGetIntegerv(GL.GL_TEXTURE_BINDING_2D)
    last_active_texture = GL.glGetIntegerv(GL.GL_ACTIVE_TEXTURE)
    last_array_buffer = GL.glGetIntegerv(GL.GL_ARRAY_BUFFER_BINDING)
    last_element_array_buffer = GL.glGetIntegerv(
        GL.GL_ELEMENT_ARRAY_BUFFER_BINDING)
    last_vertex_array = GL.glGetIntegerv(GL.GL_VERTEX_ARRAY_BINDING)
    last_blend_src = GL.glGetIntegerv(GL.GL_BLEND_SRC)
    last_blend_dst = GL.glGetIntegerv(GL.GL_BLEND_DST)
    last_blend_equation_rgb = GL. glGetIntegerv(GL.GL_BLEND_EQUATION_RGB)
    last_blend_equation_alpha = GL.glGetIntegerv(
        GL.GL_BLEND_EQUATION_ALPHA)
    last_viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
    last_scissor_box = GL.glGetIntegerv(GL.GL_SCISSOR_BOX)
    last_enable_blend = GL.glIsEnabled(GL.GL_BLEND)
    last_enable_cull_face = GL.glIsEnabled(GL.GL_CULL_FACE)
    last_enable_depth_test = GL.glIsEnabled(GL.GL_DEPTH_TEST)
    last_enable_scissor_test = GL.glIsEnabled(GL.GL_SCISSOR_TEST)
    try:
        yield
    finally:
        # restore modified GL state
        GL.glUseProgram(last_program)
        GL.glActiveTexture(last_active_texture)
        GL.glBindTexture(GL.GL_TEXTURE_2D, last_texture)
        GL.glBindVertexArray(last_vertex_array)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, last_array_buffer)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER,
                        last_element_array_buffer)
        GL.glBlendEquationSeparate(
            last_blend_equation_rgb, last_blend_equation_alpha)
        GL.glBlendFunc(last_blend_src, last_blend_dst)

        if last_enable_blend:
            GL.glEnable(GL.GL_BLEND)
        else:
            GL.glDisable(GL.GL_BLEND)

        if last_enable_cull_face:
            GL.glEnable(GL.GL_CULL_FACE)
        else:
            GL.glDisable(GL.GL_CULL_FACE)

        if last_enable_depth_test:
            GL.glEnable(GL.GL_DEPTH_TEST)
        else:
            GL.glDisable(GL.GL_DEPTH_TEST)

        if last_enable_scissor_test:
            GL.glEnable(GL.GL_SCISSOR_TEST)
        else:
            GL.glDisable(GL.GL_SCISSOR_TEST)

        GL.glViewport(last_viewport[0], last_viewport[1],
                      last_viewport[2], last_viewport[3])
        GL.glScissor(last_scissor_box[0], last_scissor_box[1],
                     last_scissor_box[2], last_scissor_box[3])


class Shader:
    def __init__(self) -> None:
        self._shader_handle = GL.glCreateProgram()
        # note: no need to store shader parts handles after linking
        vertex_shader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        fragment_shader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)

        GL.glShaderSource(vertex_shader, VERTEX_SHADER_SRC)
        GL.glShaderSource(fragment_shader, FRAGMENT_SHADER_SRC)
        GL.glCompileShader(vertex_shader)
        GL.glCompileShader(fragment_shader)

        GL.glAttachShader(self._shader_handle, vertex_shader)
        GL.glAttachShader(self._shader_handle, fragment_shader)

        GL.glLinkProgram(self._shader_handle)

        # note: after linking shaders can be removed
        GL.glDeleteShader(vertex_shader)
        GL.glDeleteShader(fragment_shader)

        self._attrib_location_tex = GL.glGetUniformLocation(
            self._shader_handle, "Texture")
        self._attrib_proj_mtx = GL.glGetUniformLocation(
            self._shader_handle, "ProjMtx")
        self._attrib_location_position = GL.glGetAttribLocation(
            self._shader_handle, "Position")
        self._attrib_location_uv = GL.glGetAttribLocation(
            self._shader_handle, "UV")
        self._attrib_location_color = GL.glGetAttribLocation(
            self._shader_handle, "Color")

    def __del__(self):
        GL.glDeleteProgram(self._shader_handle)
        self._shader_handle = 0

    def enable_attributes(self):
        GL.glEnableVertexAttribArray(self._attrib_location_position)
        GL.glEnableVertexAttribArray(self._attrib_location_uv)
        GL.glEnableVertexAttribArray(self._attrib_location_color)
        GL.glVertexAttribPointer(self._attrib_location_position, 2, GL.GL_FLOAT, GL.GL_FALSE,
                                 20, ctypes.c_void_p(0))
        GL.glVertexAttribPointer(self._attrib_location_uv, 2, GL.GL_FLOAT, GL.GL_FALSE,
                                 20, ctypes.c_void_p(8))
        GL.glVertexAttribPointer(self._attrib_location_color, 4, GL.GL_UNSIGNED_BYTE, GL.GL_TRUE,
                                 20, ctypes.c_void_p(16))

    def use(self, w: int, h: int):
        ortho_projection = (ctypes.c_float * 16)(
            2.0/w, 0.0,                   0.0, 0.0,
            0.0,               2.0/-h,   0.0, 0.0,
            0.0,               0.0,                  -1.0, 0.0,
            -1.0,               1.0,                   0.0, 1.0
        )
        GL.glUseProgram(self._shader_handle)
        GL.glUniform1i(self._attrib_location_tex, 0)
        GL.glUniformMatrix4fv(self._attrib_proj_mtx, 1,
                              GL.GL_FALSE, ortho_projection)


class Texture:
    def __init__(self, pixels: ctypes.c_void_p, width: int, height: int) -> None:
        self._font_texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._font_texture)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, width,
                        height, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pixels)

    def __del__(self):
        if self._font_texture > -1:
            GL.glDeleteTextures([self._font_texture])
        self._font_texture = 0

    @property
    def pointer(self) -> ctypes.c_void_p:
        return ctypes.c_void_p(int(self._font_texture))


class VertexBuffer:
    def __init__(self) -> None:
        self._vbo_handle = GL.glGenBuffers(1)
        self._elements_handle = GL.glGenBuffers(1)
        self._vao_handle = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self._vao_handle)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo_handle)

    def __del__(self):
        if self._vao_handle > -1:
            GL.glDeleteVertexArrays(1, [self._vao_handle])
        if self._vbo_handle > -1:
            GL.glDeleteBuffers(1, [self._vbo_handle])
        if self._elements_handle > -1:
            GL.glDeleteBuffers(1, [self._elements_handle])
        self._vao_handle = self._vbo_handle = self._elements_handle = 0

    def bind(self):
        GL.glBindVertexArray(self._vao_handle)

    def data(self, vertices: ctypes.c_void_p, vertices_size: int, indices: ctypes.c_void_p, indices_size: int):
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo_handle)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices_size,
                        vertices, GL.GL_STREAM_DRAW)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._elements_handle)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, indices_size,
                        indices, GL.GL_STREAM_DRAW)

    def draw(self, offset: int, count: int):
        GL.glDrawElements(GL.GL_TRIANGLES, count,
                          GL.GL_UNSIGNED_SHORT, ctypes.c_void_p(offset))


class Renderer:
    """Basic OpenGL integration base class."""

    def __init__(self):
        with save_state():
            self._shader = Shader()
            self._vertices = VertexBuffer()
            self._shader.enable_attributes()
        self._texture = None
        self.refresh_font_texture()

    def __del__(self):
        del self._vertices
        del self._shader
        del self._texture
        io = imgui.GetIO()
        io.fonts.TexID = 0

    def refresh_font_texture(self):
        if self._texture:
            del self._texture

        # save texture state
        with save_texture():

            io = imgui.GetIO()
            fonts = io.Fonts
            p = (ctypes.c_void_p * 1)()
            width = (ctypes.c_int * 1)()
            height = (ctypes.c_int * 1)()
            channels = (ctypes.c_int * 1)()
            fonts.GetTexDataAsRGBA32(p, width, height, channels)
            pixels = (ctypes.c_ubyte *
                      (width[0] * height[0] * channels[0])).from_address(p[0])

            self._texture = Texture(pixels, width[0], height[0])
            fonts.TexID = self._texture.pointer

        fonts.ClearTexData()

    def render(self, draw_data):
        # perf: local for faster access
        io = imgui.GetIO()

        display_width = io.DisplaySize.x
        display_height = io.DisplaySize.y
        fb_width = int(display_width * io.DisplayFramebufferScale.x)
        fb_height = int(display_height * io.DisplayFramebufferScale.y)

        if fb_width == 0 or fb_height == 0:
            return

        # ToDo:
        # draw_data.scale_clip_rects(io.FramebufferScale.x, io.FramebufferScale.y)

        # backup GL state
        # todo: provide cleaner version of this backup-restore code
        with save_render_state():
            GL.glEnable(GL.GL_BLEND)
            GL.glBlendEquation(GL.GL_FUNC_ADD)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            GL.glDisable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glEnable(GL.GL_SCISSOR_TEST)
            GL.glActiveTexture(GL.GL_TEXTURE0)

            GL.glViewport(0, 0, int(fb_width), int(fb_height))

            self._shader.use(display_width, display_height)
            self._vertices.bind()

            if draw_data.CmdLists:
                cmd_lists = ctypes.cast(draw_data.CmdLists, ctypes.POINTER(
                    ctypes.POINTER(imgui.ImDrawList)))
                # for commands in cmd_lists:
                for i in range(draw_data.CmdListsCount):
                    commands = cmd_lists[i][0]
                    idx_buffer_offset = 0

                    self._vertices.data(
                        ctypes.c_void_p(
                            commands.VtxBuffer.Data), commands.VtxBuffer.Size * 20,
                        ctypes.c_void_p(
                            commands.IdxBuffer.Data), commands.IdxBuffer.Size * 2)

                    # todo: allow to iterate over _CmdList
                    cmd_data = ctypes.cast(
                        commands.CmdBuffer.Data, ctypes.POINTER(imgui.ImDrawCmd))
                    for j in range(commands.CmdBuffer.Size):
                        command = cmd_data[j]

                        GL.glBindTexture(GL.GL_TEXTURE_2D, command.TextureId)

                        # todo: use named tuple
                        rect = command.ClipRect
                        GL.glScissor(int(rect.x), int(fb_height - rect.w),
                                     int(rect.z - rect.x), int(rect.w - rect.y))

                        self._vertices.draw(
                            idx_buffer_offset, command.ElemCount)
                        idx_buffer_offset += command.ElemCount * 2
