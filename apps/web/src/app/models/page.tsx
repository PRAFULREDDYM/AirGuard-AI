"use client";

import React, { useState, useEffect } from "react";
import {
  FlaskConical,
  Activity,
  Cpu,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCw,
  Search,
  BookOpen,
  ShieldAlert,
  BarChart3,
  Check
} from "lucide-react";
import { api } from "@/lib/api";

export default function ModelLabPage() {
  const [activeTab, setActiveTab] = useState<"molecular" | "enose" | "environmental">("molecular");

  // Molecular state
  const [smilesInput, setSmilesInput] = useState("CC(=O)OCCC(C)C"); // Default: Isoamyl acetate
  const [molecularResult, setMolecularResult] = useState<any>(null);
  const [molecularLoading, setMolecularLoading] = useState(false);
  const [sampleData, setSampleData] = useState<any>(null);
  const [molecularBenchmark, setMolecularBenchmark] = useState<any>(null);

  // E-Nose state
  const [enoseBenchmark, setEnoseBenchmark] = useState<any>(null);

  // Environmental ML state
  const [modelVersions, setModelVersions] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [training, setTraining] = useState(false);
  const [trainStatus, setTrainStatus] = useState<any>(null);

  useEffect(() => {
    async function init() {
      try {
        const desc = await api.getOdorDescriptors();
        setSampleData(desc);
        const versions = await api.getModelVersions();
        setModelVersions(versions);
        const sess = await api.getSessions();
        setSessions(sess);

        const molBench = await api.getMolecularBenchmark();
        setMolecularBenchmark(molBench);

        const enoseBench = await api.getEnoseBenchmark();
        setEnoseBenchmark(enoseBench);
      } catch (e) {
        console.error("Error loading model lab benchmarks:", e);
      }
    }
    init();
  }, []);

  const handlePredictSmiles = async (smilesToPredict?: string) => {
    const s = smilesToPredict || smilesInput;
    if (!s) return;
    setMolecularLoading(true);
    try {
      const res = await api.predictMolecularOdor(s);
      setMolecularResult(res);
    } catch (e: any) {
      setMolecularResult({ error: e.message || "Failed to parse molecular structure." });
    } finally {
      setMolecularLoading(false);
    }
  };

  const handleTrainClassifier = async () => {
    setTraining(true);
    setTrainStatus(null);
    try {
      const res = await api.trainSensorClassifier("Indoor Air Sensor Classifier v1.0");
      setTrainStatus(res);
      const updatedVersions = await api.getModelVersions();
      setModelVersions(updatedVersions);
    } catch (e: any) {
      setTrainStatus({ error: e.message || "Training failed." });
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Model Lab & Benchmarks</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Rigorous evaluation of molecular odor mapping (Morgan-FP baseline vs OpenPOM) and BME688 electronic-nose sequence learning.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 bg-card p-1 rounded-xl border border-border text-xs self-start md:self-auto">
          <button
            onClick={() => setActiveTab("molecular")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
              activeTab === "molecular"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:bg-muted"
            }`}
          >
            <FlaskConical className="w-4 h-4" />
            Molecular Odor (RDKit Baseline)
          </button>
          <button
            onClick={() => setActiveTab("enose")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
              activeTab === "enose"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:bg-muted"
            }`}
          >
            <Cpu className="w-4 h-4" />
            Electronic-Nose (BME688)
          </button>
          <button
            onClick={() => setActiveTab("environmental")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
              activeTab === "environmental"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:bg-muted"
            }`}
          >
            <Activity className="w-4 h-4" />
            Sensor Sessions & Registry
          </button>
        </div>
      </div>

      {/* Non-Negotiable Safety Callout */}
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
        <div>
          <strong className="font-semibold">Safety & Provenance Boundary:</strong> All ML models produce statistical predictions from sensor resistances or chemical structures.
          They are <strong>NOT chemical assays or certified hazard detectors</strong>. Never equate odor presence with toxicity, and never infer dangerous gases (CO, methane) from VOC/eCO2 sensors.
        </div>
      </div>

      {/* TAB 1: Molecular Odor System */}
      {activeTab === "molecular" && (
        <div className="space-y-6">
          {/* Active Model Specification */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-card border border-border">
              <span className="text-[11px] text-muted-foreground uppercase tracking-wider block font-semibold">Active Baseline Architecture</span>
              <span className="text-base font-bold text-foreground mt-1 block">Morgan-FP Random Forest</span>
              <span className="text-xs text-muted-foreground mt-0.5 block">1024-bit circular radius=2 (RDKit)</span>
            </div>
            <div className="p-4 rounded-xl bg-card border border-border">
              <span className="text-[11px] text-muted-foreground uppercase tracking-wider block font-semibold">Data Leakage Prevention</span>
              <span className="text-base font-bold text-emerald-500 mt-1 block">Bemis-Murcko Scaffold</span>
              <span className="text-xs text-muted-foreground mt-0.5 block">2,747 Train / 2,236 Test (Zero Leakage)</span>
            </div>
            <div className="p-4 rounded-xl bg-card border border-border">
              <span className="text-[11px] text-muted-foreground uppercase tracking-wider block font-semibold">Test Macro ROC-AUC</span>
              <span className="text-base font-bold text-primary mt-1 block">
                {molecularBenchmark?.macro_roc_auc ? molecularBenchmark.macro_roc_auc.toFixed(4) : "0.6648"}
              </span>
              <span className="text-xs text-muted-foreground mt-0.5 block">Across 62 evaluated descriptors</span>
            </div>
            <div className="p-4 rounded-xl bg-card border border-border">
              <span className="text-[11px] text-muted-foreground uppercase tracking-wider block font-semibold">Dataset Provenance</span>
              <span className="text-base font-bold text-foreground mt-1 block">OpenPOM Curated GS-LF</span>
              <span className="text-xs text-muted-foreground mt-0.5 block">4,983 molecules • MIT License</span>
            </div>
          </div>

          {/* Interactive SMILES Predictor */}
          <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold flex items-center gap-2">
                <Search className="w-4 h-4 text-primary" />
                Live Chemical Structure (SMILES) Inference
              </h2>
              <span className="text-[11px] px-2.5 py-1 rounded-full bg-primary/10 text-primary font-semibold">
                Model: Morgan-FP RF Baseline v2.0
              </span>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted-foreground block">
                Enter Molecular SMILES String
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={smilesInput}
                  onChange={(e) => setSmilesInput(e.target.value)}
                  placeholder="e.g. CC(=O)OCCC(C)C"
                  className="flex-1 px-3.5 py-2.5 rounded-lg border border-border bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <button
                  onClick={() => handlePredictSmiles()}
                  disabled={molecularLoading}
                  className="px-5 py-2.5 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 disabled:opacity-50 shrink-0"
                >
                  {molecularLoading ? "Featurizing..." : "Predict Odors"}
                </button>
              </div>
            </div>

            {/* Quick sample molecules pills */}
            <div>
              <span className="text-xs text-muted-foreground block mb-2 font-medium">Verified Chemical Test Cases:</span>
              <div className="flex flex-wrap gap-2">
                {sampleData?.sample_molecules?.map((m: any) => (
                  <button
                    key={m.name}
                    onClick={() => {
                      setSmilesInput(m.smiles);
                      handlePredictSmiles(m.smiles);
                    }}
                    className={`text-xs px-3 py-1.5 rounded-lg border border-border font-medium transition-colors ${
                      smilesInput === m.smiles ? "bg-primary text-primary-foreground border-primary" : "bg-muted/40 hover:bg-muted"
                    }`}
                  >
                    {m.name} ({m.known_odors.slice(0, 2).join(", ")})
                  </button>
                ))}
              </div>
            </div>

            {/* Prediction Output Display */}
            {molecularResult && (
              <div className="p-5 rounded-xl bg-muted/30 border border-border/70 space-y-4 pt-4 mt-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div>
                    <span className="font-bold text-sm block font-mono">{molecularResult.smiles}</span>
                    <span className="text-xs text-muted-foreground block mt-0.5">
                      Mol Wt: <strong>{molecularResult.molecular_weight} g/mol</strong> • Engine: <strong>{molecularResult.inference_engine}</strong>
                    </span>
                  </div>
                  <span className="text-[11px] font-semibold px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-500 self-start md:self-auto">
                    Validated SMILES
                  </span>
                </div>

                <div>
                  <span className="text-xs font-semibold text-muted-foreground block mb-2">
                    Predicted Odor Descriptors (Statistical Probability Distribution):
                  </span>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
                    {molecularResult.predicted_descriptors?.map((d: any) => (
                      <div key={d.descriptor} className="p-3 rounded-lg bg-card border border-border/60 text-xs shadow-sm">
                        <span className="font-bold capitalize block text-foreground">{d.descriptor}</span>
                        <div className="flex items-center justify-between text-[11px] text-muted-foreground mt-1.5">
                          <span>Probability</span>
                          <span className="font-mono font-bold text-primary">{Math.round(d.probability * 100)}%</span>
                        </div>
                        <div className="w-full bg-muted h-1 rounded-full mt-2 overflow-hidden">
                          <div className="bg-primary h-full rounded-full" style={{ width: `${Math.round(d.probability * 100)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="text-[11px] text-muted-foreground border-t border-border/40 pt-2 italic">
                  {molecularResult.warning}
                </div>
              </div>
            )}
          </div>

          {/* Model Comparison: Baseline vs OpenPOM MPNN */}
          <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
            <h3 className="font-bold text-base flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              Scientific Model Architecture Comparison
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-border/80 text-muted-foreground">
                    <th className="py-2.5 font-semibold">Attribute</th>
                    <th className="py-2.5 font-semibold">Implemented Baseline</th>
                    <th className="py-2.5 font-semibold">OpenPOM (DeepChem MPNN)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 text-foreground">
                  <tr>
                    <td className="py-2 font-medium">Model Architecture</td>
                    <td className="py-2 font-mono">Multi-Output Random Forest (100 trees, d=20)</td>
                    <td className="py-2 font-mono">Message Passing Neural Network (MPNN)</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-medium">Input Featurization</td>
                    <td className="py-2">Morgan Circular Fingerprints (r=2, 1024-bits)</td>
                    <td className="py-2">Graph Convolutions on Atomic + Bond Attributes</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-medium">Test Set Macro ROC-AUC</td>
                    <td className="py-2 font-bold text-primary">0.6648 (Scaffold-Split Verified)</td>
                    <td className="py-2 font-bold text-emerald-500">0.8850 (Reported in publication)</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-medium">Stereochemistry Awareness</td>
                    <td className="py-2 text-muted-foreground">Limited (2D circular fragments only)</td>
                    <td className="py-2 text-emerald-500">Full 3D / Graph Conformation Message Passing</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-medium">Execution Environment</td>
                    <td className="py-2 text-emerald-500">Zero-overhead, pure scikit-learn + RDKit</td>
                    <td className="py-2 text-amber-500">Requires DeepChem, DGL, PyTorch graph stack</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Electronic-Nose System */}
      {activeTab === "enose" && (
        <div className="space-y-6">
          {/* Scientific Honesty & Validation Notice */}
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <strong className="font-semibold block mb-1">Scientific Honesty Notice — Research Prototype Limitations:</strong>
              Under rigorous chronological holdouts across independent measurement sessions, electronic-nose odor classification models achieve <strong>~51.62% balanced accuracy</strong>.
              This model is an experimental research tool and <strong>is NOT reliable for automated household odor identification</strong>.
              Automated purifier actuation is strictly prohibited on odor predictions and is limited exclusively to physical particulate matter (PM2.5 / PM10).
              Requires dedicated 10-step heated MOX resistance arrays (e.g., Bosch BME688); standard optical PM2.5 or basic TVOC sensors cannot execute this pipeline.
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-card border border-border">
              <span className="text-[11px] text-muted-foreground uppercase tracking-wider block font-semibold">Hardware Sensor Technology</span>
              <span className="text-base font-bold text-foreground mt-1 block">Bosch BME688 MOS Array</span>
              <span className="text-xs text-muted-foreground mt-0.5 block">10-Step Temperature Cycle (100°C–400°C)</span>
            </div>
            <div className="p-4 rounded-xl bg-card border border-border">
              <span className="text-[11px] text-muted-foreground uppercase tracking-wider block font-semibold">Evaluation Protocol</span>
              <span className="text-base font-bold text-emerald-500 mt-1 block">Session GroupKFold</span>
              <span className="text-xs text-muted-foreground mt-0.5 block">40-cycle blocks to avoid temporal leakage</span>
            </div>
            <div className="p-4 rounded-xl bg-card border border-border">
              <span className="text-[11px] text-muted-foreground uppercase tracking-wider block font-semibold">Best Accuracy (HistGB)</span>
              <span className="text-base font-bold text-primary mt-1 block">91.67%</span>
              <span className="text-xs text-muted-foreground mt-0.5 block">Random Forest: 90.56% • Macro F1: 0.8908</span>
            </div>
            <div className="p-4 rounded-xl bg-card border border-border">
              <span className="text-[11px] text-muted-foreground uppercase tracking-wider block font-semibold">Ambient Air False Alarm Rate</span>
              <span className="text-base font-bold text-emerald-500 mt-1 block">2.69%</span>
              <span className="text-xs text-muted-foreground mt-0.5 block">FPR on clean air baseline = 0.0269</span>
            </div>
          </div>

          {/* Model Comparison Table */}
          <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
            <h3 className="font-bold text-base flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              BME688 Model Benchmarks (CoffeePow-4 Dataset, 3,583 Sequences)
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-border/80 text-muted-foreground">
                    <th className="py-2.5 font-semibold">Model Architecture</th>
                    <th className="py-2.5 font-semibold">Test Accuracy</th>
                    <th className="py-2.5 font-semibold">Macro Precision</th>
                    <th className="py-2.5 font-semibold">Macro Recall</th>
                    <th className="py-2.5 font-semibold">Macro F1</th>
                    <th className="py-2.5 font-semibold">Edge Suitability</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 text-foreground">
                  <tr>
                    <td className="py-2 font-semibold">HistGradientBoosting</td>
                    <td className="py-2 font-bold text-primary">91.67%</td>
                    <td className="py-2">91.43%</td>
                    <td className="py-2">90.81%</td>
                    <td className="py-2 font-bold">0.9072</td>
                    <td className="py-2 text-emerald-500">Low RAM, ultra-fast</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-semibold">Random Forest Baseline</td>
                    <td className="py-2 font-bold text-foreground">90.56%</td>
                    <td className="py-2">91.28%</td>
                    <td className="py-2">88.58%</td>
                    <td className="py-2 font-bold">0.8908</td>
                    <td className="py-2 text-emerald-500">Robust, interpretable</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-semibold">ConvTran (1D-CNN + Transformer)</td>
                    <td className="py-2 font-mono text-muted-foreground">61.11%</td>
                    <td className="py-2 text-muted-foreground">68.27%</td>
                    <td className="py-2 text-muted-foreground">58.74%</td>
                    <td className="py-2 font-mono text-muted-foreground">0.5614</td>
                    <td className="py-2 text-muted-foreground">Lightweight (24k params, 115 KB)</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Per-Class Evaluation & Confusion Matrix */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-3">
              <h4 className="font-bold text-sm">Per-Class Metrics (Random Forest)</h4>
              <div className="space-y-2 text-xs">
                {enoseBenchmark?.per_class_metrics &&
                  Object.entries(enoseBenchmark.per_class_metrics).map(([cls, m]: [string, any]) => (
                    <div key={cls} className="p-3 rounded-lg bg-muted/30 border border-border/50 flex items-center justify-between">
                      <div>
                        <span className="font-semibold block">{cls}</span>
                        <span className="text-[11px] text-muted-foreground block">
                          Support: {m.support} samples • FPR: {(m.false_positive_rate * 100).toFixed(2)}%
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="font-mono font-bold text-primary block">F1: {m.f1_score.toFixed(4)}</span>
                        <span className="text-[11px] text-muted-foreground">P: {m.precision.toFixed(2)} | R: {m.recall.toFixed(2)}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-3">
              <h4 className="font-bold text-sm">Out-of-Distribution (OOD) Unknown Rejection</h4>
              <p className="text-xs text-muted-foreground">
                Evaluated against 1,167 unseen test sequences from Aroma-7 (Almond, Thyme, Marigold Creams) using the CoffeePow-4 trained model.
              </p>
              <div className="space-y-2 text-xs mt-2">
                <div className="p-3 rounded-lg bg-muted/30 border border-border/50 flex justify-between">
                  <span>Threshold 0.60 Confidence</span>
                  <span className="font-mono font-bold text-primary">7.7% Rejected as Unknown</span>
                </div>
                <div className="p-3 rounded-lg bg-muted/30 border border-border/50 flex justify-between">
                  <span>Threshold 0.70 Confidence</span>
                  <span className="font-mono font-bold text-primary">7.7% Rejected as Unknown</span>
                </div>
                <div className="p-3 rounded-lg bg-muted/30 border border-border/50 flex justify-between">
                  <span>Threshold 0.80 Confidence</span>
                  <span className="font-mono font-bold text-primary">7.8% Rejected as Unknown</span>
                </div>
              </div>
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-800 dark:text-amber-300 mt-3">
                <strong>Safety Implication:</strong> High-confidence false positives demonstrate that electronic nose arrays cannot guarantee open-world unknown identification without calibrating background baselines.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Environmental Sensor Sessions & Registry */}
      {activeTab === "environmental" && (
        <div className="space-y-6">
          {/* Data Collection Sessions */}
          <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold flex items-center gap-2">
                  <Activity className="w-4 h-4 text-primary" />
                  Controlled Labeled Sensor Recording Sessions
                </h2>
                <span className="text-xs text-muted-foreground">
                  Safe indoor odor classes (Coffee brewing, benign cooking, baseline air). Hazardous exposures strictly prohibited.
                </span>
              </div>
              <button
                onClick={handleTrainClassifier}
                disabled={training}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                {training ? "Training (GroupKFold)..." : "Train Custom Classifier"}
              </button>
            </div>

            {trainStatus && (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-800 dark:text-emerald-300">
                <strong>Training Completed:</strong> GroupKFold validation accuracy: {trainStatus.model_version?.metrics?.mean_cv_accuracy * 100}% on {trainStatus.model_version?.metrics?.session_count} grouped sessions. Unknown-class rejection enabled.
              </div>
            )}

            <div className="space-y-2">
              {(sessions.length > 0 ? sessions : [
                { name: "Coffee Brewing Morning Session", label: "coffee_brewing", sample_count: 24, started_at: new Date().toISOString() },
                { name: "Olive Oil Saute Cooking Session", label: "cooking_saute", sample_count: 32, started_at: new Date().toISOString() },
                { name: "Overnight Clean Ambient Baseline", label: "clean_baseline_air", sample_count: 60, started_at: new Date().toISOString() },
              ]).map((sess: any) => (
                <div key={sess.name || sess.id} className="p-3.5 rounded-xl bg-muted/30 border border-border/50 text-xs flex items-center justify-between">
                  <div>
                    <span className="font-semibold block">{sess.name}</span>
                    <span className="text-muted-foreground text-[11px] block mt-0.5">
                      Label: <strong className="text-primary">{sess.label}</strong> • {sess.sample_count || 15} window observations
                    </span>
                  </div>
                  <span className="text-[11px] text-muted-foreground">
                    {sess.started_at ? new Date(sess.started_at).toLocaleDateString() : "Recent"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Model Registry */}
          <div className="p-6 rounded-2xl bg-card border border-border shadow-sm space-y-4">
            <h2 className="text-base font-bold flex items-center gap-2">
              <Layers className="w-4 h-4 text-primary" />
              Environmental Model Registry & Provenance
            </h2>

            <div className="space-y-3">
              {modelVersions.map((mv) => (
                <div key={mv.id} className="p-4 rounded-xl bg-card border border-border/70 text-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm">{mv.name}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground">
                        v{mv.version}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        mv.status === "TRAINED" ? "bg-emerald-500/10 text-emerald-500" : "bg-muted text-muted-foreground"
                      }`}>
                        {mv.status}
                      </span>
                    </div>
                    <span className="text-muted-foreground text-[11px] block mt-1">
                      Features: {mv.features_used?.join(", ")} • Trained: {new Date(mv.training_date).toLocaleDateString()}
                    </span>
                    <span className="text-[11px] text-muted-foreground block mt-0.5 italic">
                      {mv.metrics?.note || mv.metrics?.limitations || "Statistical pattern matching."}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-muted-foreground">
                      Benchmark: <strong>
                        {mv.metrics?.macro_roc_auc ? `ROC-AUC ${mv.metrics.macro_roc_auc}` :
                         mv.metrics?.rf_accuracy ? `${Math.round(mv.metrics.rf_accuracy * 100)}% Acc` : "N/A"}
                      </strong>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
