import logging
import imgui


class ImGuiLogHandler(logging.Handler):
    '''
    Logger
    '''
    def __init__(self):
        super().__init__()
        self.logs = []
        self.open = True

    def emit(self, record):
        msg = self.format(record)
        if not msg.endswith("\n"):
            msg += "\n"
        self.logs.append(msg)

    def write(self, m):
        pass


    def draw(self):
        self.open
        expanded, self.open = imgui.begin('log', self.open)
        if self.open:
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

            # ImGui::EndChild();

        imgui.end()
