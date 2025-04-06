import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [documentFile, setDocumentFile] = useState(null);
  const [activeTab, setActiveTab] = useState("chat");
  const [savedQueries, setSavedQueries] = useState([]);
  const [uploadedDocuments, setUploadedDocuments] = useState([]);
  const [lastResponseId, setLastResponseId] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  // Load initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [queriesRes, docsRes] = await Promise.all([
          fetch("http://127.0.0.1:5000/api/get_queries"),
          fetch("http://127.0.0.1:5000/api/get_documents")
        ]);
        setSavedQueries(await queriesRes.json());
        setUploadedDocuments(await docsRes.json());
      } catch (error) {
        console.error("Error loading data:", error);
      }
    };
    fetchData();
  }, []);

  const handleSend = async () => {
    if (!message.trim()) return;

    const userMessage = message;
    setChatHistory((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const response = await fetch("http://127.0.0.1:5000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await response.json();
      const botResponse = data.response;
      const responseId = Date.now();
      
      setChatHistory((prev) => [
        ...prev, 
        { 
          role: "bot", 
          content: botResponse,
          responseId: responseId 
        }
      ]);
      setLastResponseId(responseId);

      await fetch("http://127.0.0.1:5000/api/save_query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userMessage,
          answer: botResponse,
          document: documentFile?.name || "Current Document",
        }),
      });

      const queriesResponse = await fetch("http://127.0.0.1:5000/api/get_queries");
      setSavedQueries(await queriesResponse.json());

    } catch (error) {
      console.error("Error:", error);
      setChatHistory((prev) => [
        ...prev,
        { role: "bot", content: "Sorry, something went wrong. Please try again." },
      ]);
    }
    setMessage("");
  };

  const handleFeedback = async (responseId, rating) => {
    const botMessage = chatHistory.find(msg => msg.responseId === responseId);
    if (!botMessage) return;

    try {
      await fetch("http://127.0.0.1:5000/api/log_feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: chatHistory[chatHistory.length - 2].content,
          response: botMessage.content,
          rating: rating,
          comments: rating === "thumbs_down" 
            ? prompt("What was inaccurate about this response?") 
            : ""
        }),
      });
      alert("Thank you for your feedback!");
    } catch (error) {
      console.error("Feedback submission failed:", error);
    }
  };

  const handleDocumentUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setDocumentFile(file);
    setUploadError(null);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:5000/api/upload_document", {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Upload failed");
      }
      
      const data = await response.json();
      setUploadedDocuments(prev => [...prev, {
        filename: data.filename,
        upload_time: new Date().toISOString()
      }]);
      alert(data.message);
    } catch (error) {
      console.error("Upload error:", error);
      setUploadError(error.message);
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>Document Q&A Chatbot</h1>
        <div className="tabs">
          <button className={`tab-button ${activeTab === "chat" ? "active" : ""}`} onClick={() => setActiveTab("chat")}>
            Chat
          </button>
          <button className={`tab-button ${activeTab === "history" ? "active" : ""}`} onClick={() => setActiveTab("history")}>
            Chat History
          </button>
          <button className={`tab-button ${activeTab === "documents" ? "active" : ""}`} onClick={() => setActiveTab("documents")}>
            Uploaded Files
          </button>
        </div>
      </header>

      {activeTab === "chat" ? (
        <>
          <div className="chat-history">
            {uploadError && <div className="error-message">{uploadError}</div>}
            {chatHistory.map((chat, index) => (
              <div key={index} className={`chat-message ${chat.role === "user" ? "user-message" : "bot-message"}`}>
                {chat.content}
                {chat.role === "bot" && (
                  <div className="feedback-buttons">
                    <button onClick={() => handleFeedback(chat.responseId, "thumbs_up")}>👍</button>
                    <button onClick={() => handleFeedback(chat.responseId, "thumbs_down")}>👎</button>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="chat-input-container">
            <input type="file" id="document-upload" accept=".pdf,.txt,.docx" onChange={handleDocumentUpload} />
            <label htmlFor="document-upload" className="upload-button">📁 Upload Document</label>
            <input
              type="text"
              className="chat-input"
              placeholder="Ask about your document..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSend()}
            />
            <button className="send-button" onClick={handleSend}>Send</button>
          </div>
        </>
      ) : activeTab === "history" ? (
        <div className="query-history">
          {savedQueries.length === 0 ? (
            <p className="no-queries">No saved queries yet</p>
          ) : (
            <div className="query-list">
              {savedQueries.map((query, index) => (
                <div key={index} className="query-item">
                  <div className="query-header">
                    <span className="document-name">{query.document}</span>
                    <span className="query-time">{new Date(query.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="question">Q: {query.question}</div>
                  <div className="answer">A: {query.answer}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="documents-list">
          <h3>Uploaded Documents ({uploadedDocuments.length})</h3>
          {uploadedDocuments.length === 0 ? (
            <p className="no-documents">No documents uploaded yet</p>
          ) : (
            <ul>
              {uploadedDocuments.map((doc, index) => (
                <li key={index}>
                  <span className="document-filename">{doc.filename}</span>
                  <span className="document-time">{new Date(doc.upload_time).toLocaleString()}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

export default App;