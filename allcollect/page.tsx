import { Suspense } from "react";
import { Studio } from "@/components/studio";

export default function HomePage() {
  return (
    <main>
      <Suspense fallback={<div className="center-state">Loading private studio…</div>}>
        <Studio />
      </Suspense>
    </main>
  );
}
