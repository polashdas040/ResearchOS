import React from "react";
import { WorkspaceShell } from "../../../components/WorkspaceShell";

type ProjectPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function ProjectPage({ params }: ProjectPageProps) {
  const { id } = await params;
  return <WorkspaceShell projectId={id} />;
}
