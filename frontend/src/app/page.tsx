"use client";

import { ReactFlowProvider } from "@xyflow/react";

import { useAppInitialization } from "@/hooks";
import { AppLayout, Sidebar, PropertiesPanel, CanvasHeader } from "@/components/layout";
import { WorkflowCanvas } from "@/components/workflow";
import PaymentModal from "@/components/PaymentModal";
import { useWorkflowStore, usePaymentStore } from "@/stores";
import { toast } from "sonner";

export default function Home() {
  useAppInitialization();

  const { workflowId, workflowName } = useWorkflowStore();
  const { isModalOpen, closeModal } = usePaymentStore();

  const handleDeploySuccess = (id: string) => {
    toast.success(`Workflow ${id.slice(0, 8)} deployed successfully!`);
  };

  const handleDeployError = (error: string) => {
    toast.error(`Deployment failed: ${error}`);
  };

  return (
    <ReactFlowProvider>
      <AppLayout
        sidebar={<Sidebar />}
        propertiesPanel={<PropertiesPanel />}
        header={<CanvasHeader />}
      >
        <WorkflowCanvas />
      </AppLayout>

      {/* Payment Modal for workflow deployment */}
      <PaymentModal
        isOpen={isModalOpen}
        onClose={closeModal}
        workflowId={workflowId || ""}
        workflowName={workflowName || undefined}
        onSuccess={handleDeploySuccess}
        onError={handleDeployError}
      />
    </ReactFlowProvider>
  );
}
