"use client";

import {
  Component,
  Suspense,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Bounds, OrbitControls, useBounds, useGLTF } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import * as THREE from "three";
import { artifactDownloadUrl } from "@/lib/api";

interface Stats {
  meshes: number;
  triangles: number;
}

class ViewerBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="viewer-error">
          The verified artifact could not be parsed by the browser viewer. Download it for
          investigation instead of treating this as a successful visual validation.
        </div>
      );
    }
    return this.props.children;
  }
}

function ResetBounds({ resetKey }: { resetKey: number }) {
  const bounds = useBounds();
  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      bounds.refresh().clip().fit();
    });
    return () => cancelAnimationFrame(frame);
  }, [bounds, resetKey]);
  return null;
}

function Asset({
  url,
  wireframe,
  resetKey,
  onStats,
}: {
  url: string;
  wireframe: boolean;
  resetKey: number;
  onStats: (stats: Stats) => void;
}) {
  const gltf = useGLTF(url);
  const prepared = useMemo(() => {
    const scene = gltf.scene.clone(true);
    let meshes = 0;
    let triangles = 0;

    scene.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) return;
      meshes += 1;
      const geometry = object.geometry;
      triangles += geometry.index
        ? Math.floor(geometry.index.count / 3)
        : Math.floor((geometry.attributes.position?.count ?? 0) / 3);
      if (Array.isArray(object.material)) {
        object.material = object.material.map((material) => material.clone());
      } else if (object.material) {
        object.material = object.material.clone();
      }
    });
    return { scene, stats: { meshes, triangles } };
  }, [gltf.scene]);

  useEffect(() => {
    prepared.scene.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) return;
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      for (const material of materials) {
        if (material && "wireframe" in material) {
          (material as THREE.MeshStandardMaterial).wireframe = wireframe;
          material.needsUpdate = true;
        }
      }
    });
  }, [prepared.scene, wireframe]);

  useEffect(() => {
    onStats(prepared.stats);
    return () => {
      prepared.scene.traverse((object) => {
        if (!(object instanceof THREE.Mesh)) return;
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        for (const material of materials) material?.dispose();
      });
    };
  }, [onStats, prepared]);

  return (
    <Bounds fit clip observe margin={1.2}>
      <primitive object={prepared.scene} />
      <ResetBounds resetKey={resetKey} />
    </Bounds>
  );
}

export function ModelViewer({ jobId }: { jobId: string }) {
  const [wireframe, setWireframe] = useState(false);
  const [resetKey, setResetKey] = useState(0);
  const [stats, setStats] = useState<Stats | null>(null);
  const url = artifactDownloadUrl(jobId);

  return (
    <div className="viewer-stack">
      <div className="viewer-toolbar">
        <label className="check-control">
          <input
            type="checkbox"
            checked={wireframe}
            onChange={(event) => setWireframe(event.target.checked)}
          />
          Wireframe
        </label>
        <button className="secondary-button compact" onClick={() => setResetKey((value) => value + 1)}>
          Reset camera
        </button>
        {stats ? (
          <span className="model-stats" data-testid="viewer-ready">
            GLB loaded · Meshes {stats.meshes} · Triangles {stats.triangles.toLocaleString()}
          </span>
        ) : (
          <span className="model-stats">Loading verified GLB…</span>
        )}
      </div>
      <ViewerBoundary key={jobId}>
        <div className="viewer-canvas">
          <Canvas camera={{ position: [3, 2, 3], fov: 45 }} gl={{ antialias: true }}>
            <color attach="background" args={["#10141b"]} />
            <ambientLight intensity={1.2} />
            <directionalLight position={[4, 6, 3]} intensity={2.4} />
            <directionalLight position={[-3, 2, -4]} intensity={1.1} />
            <gridHelper args={[10, 10, "#344052", "#232b38"]} />
            <Suspense fallback={null}>
              <Asset
                url={url}
                wireframe={wireframe}
                resetKey={resetKey}
                onStats={setStats}
              />
            </Suspense>
            <OrbitControls makeDefault enableDamping />
          </Canvas>
        </div>
      </ViewerBoundary>
    </div>
  );
}
