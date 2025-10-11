import { useState } from "react";
import { startDocumentTranslation, getJobStatus } from "../services/api";

function TranslatePage() {
  const [filePath, setFilePath] = useState("");
  const [jobId, setJobId] = useState("");
  const [output, setOutput] = useState("");

  const handleStart = async () => {
    try {
      const data = await startDocumentTranslation(filePath);
      setJobId(data.job_id);
      alert(`Started job: ${data.job_id}`);

      // Polling every 2 seconds
      const interval = setInterval(async () => {
        const statusData = await getJobStatus(data.job_id);
        console.log(statusData);

        if (statusData.status === "completed") {
          setOutput(statusData.result);
          clearInterval(interval);
        }
      }, 2000);
    } catch (err) {
      console.error(err);
      alert("Something went wrong!");
    }
  };

  return (
    <div style={{ padding: "1rem" }}>
      <h2>Document Translation</h2>

      <input
        type="text"
        placeholder="Enter file path..."
        value={filePath}
        onChange={(e) => setFilePath(e.target.value)}
        style={{ width: "300px", marginRight: "1rem" }}
      />
      <button onClick={handleStart}>Start Translation</button>

      {jobId && <p>Job ID: {jobId}</p>}
      {output && (
        <div style={{ marginTop: "1rem" }}>
          <h4>Translated Output:</h4>
          <pre>{JSON.stringify(output, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default TranslatePage;
