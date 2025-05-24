import React, { useState } from 'react';
import './App.css'; // We'll use this for basic styling

function App() {
  const [inputText, setInputText] = useState('');
  const [reportType, setReportType] = useState('Summarize Clinical Notes'); // Default report type
  const [generatedReport, setGeneratedReport] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const availableReportTypes = [
    "Summarize Clinical Notes",
    "Explain Medical Terminology",
    // Add more types as you implement them in the backend
    // "Draft Patient Communication",
    // "Generate Differential Diagnosis Ideas"
  ];

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsLoading(true);
    setError('');
    setGeneratedReport('');

    // --- API Call Logic will go here ---
    console.log("Submitting:", { inputText, reportType });
    
    // Placeholder for now:
    // Simulating API call
    try {
      // Replace with actual fetch call to your backend
      const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:5001'; // Get from .env or default
      const response = await fetch(`${backendUrl}/api/generate-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          inputText: inputText,
          reportType: reportType,
        }),
      });

      if (!response.ok) {
        // Try to get error message from backend's JSON response
        let errorData;
        try {
          errorData = await response.json();
        } catch (e) {
          // If response is not JSON or other error
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.report) {
        setGeneratedReport(data.report);
      } else {
        setError("Received an empty report from the server.");
      }

    } catch (err) {
      console.error("API Call Error:", err);
      setError(err.message || "An unknown error occurred while fetching the report.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Medical Report Generator (with MedGemma)</h1>
        <p className="disclaimer">
          <strong>Disclaimer:</strong> For Research & Informational Purposes Only. 
          NOT a substitute for professional medical advice, diagnosis, or treatment. 
          Verify all information.
        </p>
      </header>

      <main className="App-main">
        <form onSubmit={handleSubmit} className="report-form">
          <div className="form-group">
            <label htmlFor="inputText">Clinical Notes / Input Text:</label>
            <textarea
              id="inputText"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              rows="10"
              placeholder="Enter de-identified clinical notes, symptoms, lab results, etc."
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="reportType">Select Report Type:</label>
            <select
              id="reportType"
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
            >
              {availableReportTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Generating...' : 'Generate Report'}
          </button>
        </form>

        {error && <div className="error-message">Error: {error}</div>}

        {generatedReport && (
          <div className="report-output">
            <h2>Generated Report:</h2>
            <pre>{generatedReport}</pre> {/* Using <pre> to preserve formatting like newlines */}
            <button onClick={() => navigator.clipboard.writeText(generatedReport)}>
              Copy to Clipboard
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;