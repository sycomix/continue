import os
from typing import List

from pydantic import Field
from ripgrepy import Ripgrepy

from ...core.context import ContextProvider
from ...core.main import ContextItem, ContextItemDescription, ContextItemId
from ...libs.util.logging import logger
from .util import remove_meilisearch_disallowed_chars


class SearchContextProvider(ContextProvider):
    """Type '@search' to reference the results of codebase search, just like the results you would get from VS Code search."""

    title = "search"
    display_title = "Search"
    description = "Search the workspace for all matches of an exact string (e.g. '@search console.log')"
    dynamic = True
    requires_query = True

    _SEARCH_CONTEXT_ITEM_ID = "search"

    workspace_dir: str = Field(None, description="The workspace directory to search")

    @property
    def BASE_CONTEXT_ITEM(self):
        return ContextItem(
            content="",
            description=ContextItemDescription(
                name="Search",
                description="Search the workspace for all matches of an exact string (e.g. '@search console.log')",
                id=ContextItemId(
                    provider_title=self.title, item_id=self._SEARCH_CONTEXT_ITEM_ID
                ),
            ),
        )

    def _get_rg_path(self):
        if os.name == "nt":
            paths_to_try = [
                f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Programs\\Microsoft VS Code\\resources\\app\\node_modules.asar.unpacked\\@vscode\\ripgrep\\bin\\rg.exe",
                f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Programs\\Microsoft VS Code\\resources\\app\\node_modules.asar.unpacked\\vscode-ripgrep\\bin\\rg.exe",
            ]
            for path in paths_to_try:
                if os.path.exists(path):
                    rg_path = path
                    break
        elif os.name == "posix":
            if "darwin" in os.sys.platform:
                rg_path = "/Applications/Visual Studio Code.app/Contents/Resources/app/node_modules.asar.unpacked/@vscode/ripgrep/bin/rg"
            else:
                rg_path = "/usr/share/code/resources/app/node_modules.asar.unpacked/vscode-ripgrep/bin/rg"
        else:
            rg_path = "rg"

        if not os.path.exists(rg_path):
            rg_path = "rg"

        return rg_path

    async def _search(self, query: str) -> str:
        rg = Ripgrepy(query, self.workspace_dir, rg_path=self._get_rg_path())
        results = rg.I().context(2).run()
        return f"Search results in workspace for '{query}':\n\n{results}"

    async def provide_context_items(self, workspace_dir: str) -> List[ContextItem]:
        self.workspace_dir = workspace_dir

        try:
            Ripgrepy("", workspace_dir, rg_path=self._get_rg_path())
        except Exception as e:
            logger.warning(f"Failed to initialize ripgrepy: {e}")
            return []

        return [self.BASE_CONTEXT_ITEM]

    async def get_item(self, id: ContextItemId, query: str) -> ContextItem:
        if id.provider_title != self.title:
            raise Exception("Invalid provider title for item")

        query = query.lstrip("search ")
        results = await self._search(query)

        ctx_item = self.BASE_CONTEXT_ITEM.copy()
        ctx_item.content = results
        ctx_item.description.name = f"Search: '{query}'"
        ctx_item.description.id.item_id = remove_meilisearch_disallowed_chars(query)
        return ctx_item
