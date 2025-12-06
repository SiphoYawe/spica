"use client";

import { ReactFlowProvider } from "@xyflow/react";

import { useAppInitialization } from "@/hooks";
import { AppLayout, Sidebar, PropertiesPanel, CanvasHeader } from "@/components/layout";
import { WorkflowCanvas } from "@/components/workflow";

export default function Home() {
  useAppInitialization();

  return (
    <ReactFlowProvider>
      <AppLayout
        sidebar={<Sidebar />}
        propertiesPanel={<PropertiesPanel />}
        header={<CanvasHeader />}
      >
        <WorkflowCanvas />
      </AppLayout>
    </ReactFlowProvider>
  );
}
