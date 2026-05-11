import { useState } from "react";
import Head from "next/head";

interface UploadResponse {
  file_id: string;
  filename: string;
  page_count: number;
}

interface ComplianceCheck {
  check: string;
  status: string;
  details?: string;
}

interface ComplianceReport {
  report_id: string;
  filename: string;
  image_url: string;
  page_count: number;
  detections: any[];
  ocr_results: any[];
  compliance_checks: ComplianceCheck[];
  overall_status: string;
  summary: string;
}

export default function ReportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [loading, setLoading] = useState(false);
  const backendBase = "http://localhost:8000";

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const uploadFile = async (): Promise<string | null> => {
    if (!file) return null;
    const form = new FormData();
    form.append("file", file);
    const resp = await fetch(`${backendBase}/upload`, {
      method: "POST",
      body: form,
    });
    if (!resp.ok) {
      alert("Upload failed: " + (await resp.text()));
      return null;
    }
    const data = (await resp.json()) as UploadResponse;
    return data.file_id;
  };

  const analyze = async (fileId: string) => {
    const resp = await fetch(`${backendBase}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_id: fileId }),
    });
    if (!resp.ok) {
      alert("Analysis failed: " + (await resp.text()));
      return;
    }
    const data = (await resp.json()) as ComplianceReport;
    setReport(data);
  };

  const startProcess = async () => {
    setLoading(true);
    try {
      const fileId = await uploadFile();
      if (fileId) await analyze(fileId);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>AutoPermitAI – Generate Report</title>
        <meta name="description" content="Upload blueprint and generate compliance report" />
      </Head>
      <div style={{ fontFamily: "Segoe UI, Tahoma, sans-serif", padding: "2rem" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "1rem" }}>Generate Compliance Report</h1>
        <div style={{ marginBottom: "1rem" }}>
          <input type="file" accept=".pdf" onChange={handleFileChange} />
        </div>
        <button
          onClick={startProcess}
          disabled={loading || !file}
          style={{ padding: "0.5rem 1rem", background: "#4a90e2", color: "white", border: "none", borderRadius: "4px", cursor: loading || !file ? "not-allowed" : "pointer" }}
        >
          {loading ? "Processing…" : "Upload & Analyze"}
        </button>

        {report && (
          <div style={{ marginTop: "2rem", maxWidth: "800px" }}>
            <h2>{report.filename}</h2>
            <p><strong>Status:</strong> {report.overall_status}</p>
            <p><strong>Summary:</strong> {report.summary}</p>
            <img src={`${backendBase}${report.image_url}`} alt="Annotated Blueprint" style={{ marginTop: "1rem", maxWidth: "100%" }} />
            <h3 style={{ marginTop: "1rem" }}>Compliance Checks</h3>
            <ul>
              {report.compliance_checks.map((c, i) => (
                <li key={i}>
                  <strong>{c.check}:</strong> {c.status}{c.details && ` – ${c.details}`}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </>
  );
}


interface UploadResponse {
  file_id: string;
  filename: string;
  page_count: number;
}

interface ComplianceCheck {
  check: string;
  status: string;
  details?: string;
}

interface ComplianceReport {
  report_id: string;
  filename: string;
  image_url: string;
  page_count: number;
  detections: any[];
  ocr_results: any[];
  compliance_checks: ComplianceCheck[];
  overall_status: string;
  summary: string;
}

export default function ReportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [loading, setLoading] = useState(false);
  const backendBase = "http://localhost:8000"; // adjust if needed

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const uploadFile = async () => {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    const resp = await fetch(`${backendBase}/upload`, {
      method: "POST",
      body: form,
    });
    if (!resp.ok) {
      alert("Upload failed: " + (await resp.text()));
      return null;
    }
    const data = (await resp.json()) as UploadResponse;
    return data.file_id;
  };

  const analyze = async (fileId: string) => {
    const resp = await fetch(`${backendBase}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_id: fileId }),
    });
    if (!resp.ok) {
      alert("Analysis failed: " + (await resp.text()));
      return;
    }
    const data = (await resp.json()) as ComplianceReport;
    setReport(data);
  };

  const startProcess = async () => {
    setLoading(true);
    try {
      const fileId = await uploadFile();
      if (fileId) await analyze(fileId);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>AutoPermitAI – Generate Report</title>
        <style>{`
          .container {font-family: 'Segoe UI', Tahoma, sans-serif; background:#f5f8ff; min-height:100vh; display:flex; flex-direction:column; align-items:center; padding:2rem;}
          .card {background:#fff; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.08); padding:1.5rem; max-width:600px; width:100%; margin-top:1rem;}
          .title {font-size:1.8rem; margin-bottom:1rem; color:#222;}
          .button {background:#4a90e2; color:#fff; border:none; padding:0.6rem 1.2rem; border-radius:6px; cursor:pointer; width:100%; font-size:1rem;}
          .button:disabled {background:#a0c4ff; cursor:not-allowed;}
          .report-card {margin-top:2rem; background:#fff; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.07); padding:1.5rem; max-width:800px; width:100%;}
          .section {margin-top:1rem;}
          .section h2 {font-size:1.4rem; margin-bottom:0.5rem; color:#333;}
          .checks {list-style:disc inside; margin-left:0;}
          .checks li {margin-bottom:0.4rem;}
        `}</style>
      </Head>
      <div className="container">
        <h1 className="title">Generate Compliance Report</h1>
        <div className="card">
          <input type="file" accept=".pdf" onChange={handleFileChange} />
          <button
            onClick={startProcess}
            disabled={loading || !file}
            className="button"
          >
            {loading ? "Processing…" : "Upload & Analyze"}
          </button>
        </div>

        {report && (
          <div className="report-card">
            <h2>{report.filename}</h2>
            <p><strong>Status:</strong> {report.overall_status}</p>
            <p><strong>Summary:</strong> {report.summary}</p>
            <img src={`${backendBase}${report.image_url}`} alt="Annotated Blueprint" style={{maxWidth: "100%", marginTop: "1rem"}} />
            <div className="section">
              <h2>Compliance Checks</h2>
              <ul className="checks">
                {report.compliance_checks.map((c, i) => (
                  <li key={i}>
                    <strong>{c.check}:</strong> {c.status}{c.details && ` – ${c.details}`}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
