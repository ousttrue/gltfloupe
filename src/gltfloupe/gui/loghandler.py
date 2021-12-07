import logging
import imgui


class ImGuiLogHandler(logging.Handler):
    '''
    Logger
    '''

    def __init__(self):
        super().__init__()
        self.logs = []

    def emit(self, record):
        msg = self.format(record)
        if not msg.endswith("\n"):
            msg += "\n"
        self.logs.append(msg)

    def write(self, m):
        pass

    def draw(self):
        # ImGui::BeginChild("scrolling", ImVec2(0, 0), false, ImGuiWindowFlags_HorizontalScrollbar);

        # ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(0, 0));

        # ImGuiListClipper clipper;
        # clipper.Begin(LineOffsets.Size);
        # while (clipper.Step())
        for log in self.logs:
            imgui.text_unformatted(log)
        # clipper.End();

        # if (AutoScroll && ImGui::GetScrollY() >= ImGui::GetScrollMaxY())
        #     ImGui::SetScrollHereY(1.0f);

        imgui.set_scroll_here_y(1.0)

        # ImGui::EndChild();
