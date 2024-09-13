import "@mantine/core/styles.css";
import "@mantine/charts/styles.css";

import { RouterProvider, createBrowserRouter } from "react-router-dom";

import { BaseLayout } from "./layouts/BaseLayout";
import { IntroductionPage } from "./pages/IntroductionPage";
import { ChatAgentPage } from "./pages/ChatAgentPage";
import { ImportArticlesPage } from "./pages/ImportArticlesPage";
import { MantineProvider, createTheme } from "@mantine/core";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NetworkGraphPage } from "./pages/NetworkGraphPage";

const theme = createTheme({});

const router = createBrowserRouter([
  {
    path: "/",
    element: <BaseLayout />,
    children: [
      {
        path: "",
        element: <IntroductionPage />,
      },
      {
        path: "chat-agent/",
        element: <ChatAgentPage />,
      },
      {
        path: "fetch-network/",
        element: <NetworkGraphPage />,
      },
      {
        path: "import-articles/",
        element: <ImportArticlesPage />,
      },
    ],
  },
]);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: true,
      staleTime: 0,
      gcTime: 0,
    },
  },
});

export function App() {
  return (
    <MantineProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </MantineProvider>
  );
}
