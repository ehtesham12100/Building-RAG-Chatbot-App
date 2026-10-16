// State Management
let currentSessionId = null;
let selectedDocIds = []; // Empty array means query all documents
let isGenerating = false;

// DOM Elements
const dropZone = document.getElementById('dropZone');
const pdfFileInput = document.getElementById('pdfFileInput');
const uploadProgress = document.getElementById('uploadProgress');
const documentList = document.getElementById('documentList');
const docCountEl = document.getElementById('docCount');
const selectAllDocsBtn = document.getElementById('selectAllDocs');
const deselectAllDocsBtn = document.getElementById('deselectAllDocs');
const activeFilterBadge = document.getElementById('activeFilterBadge');
const chatSessionsList = document.getElementById('chatSessionsList');
const newChatBtn = document.getElementById('newChatBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const messagesContainer = document.getElementById('messagesContainer');
const welcomeBanner = document.getElementById('welcomeBanner');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const activeModelLabel = document.getElementById('activeModelLabel');

// Settings Elements
const settingsModal = document.getElementById('settingsModal');
const openSettingsBtn = document.getElementById('openSettingsBtn');
const closeSettingsBtn = document.getElementById('closeSettingsBtn');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const providerSelect = document.getElementById('providerSelect');
const geminiApiKeyInput = document.getElementById('geminiApiKeyInput');
const groqApiKeyInput = document.getElementById('groqApiKeyInput');
const topKSlider = document.getElementById('topKSlider');
const topKValue = document.getElementById('topKValue');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
  loadLocalSettings();
  await checkConfig();
  await loadDocuments();
  await loadSessions();
  setupEventListeners();
});

function loadLocalSettings() {
  const savedProvider = localStorage.getItem('rag_provider') || 'gemini';
  providerSelect.value = savedProvider;
  geminiApiKeyInput.value = localStorage.getItem('gemini_api_key') || '';
  groqApiKeyInput.value = localStorage.getItem('groq_api_key') || '';
  const savedTopK = localStorage.getItem('rag_top_k') || '4';
  topKSlider.value = savedTopK;
  topKValue.textContent = savedTopK;
  updateModelLabel();
}

function updateModelLabel() {
  const provider = providerSelect.value;
  if (provider === 'gemini') {
    activeModelLabel.textContent = 'Gemini 3.8 Flash';
  } else {
    activeModelLabel.textContent = 'Groq Llama 3.3 70B';
  }
}

async function checkConfig() {
  try {
    const res = await fetch('/api/chat/config');
    const data = await res.json();
    if (!data.gemini_configured && !localStorage.getItem('gemini_api_key')) {
      // Prompt user to enter their API key
      setTimeout(() => openSettingsModal(), 600);
    }
  } catch (err) {
    console.warn('Could not fetch config:', err);
  }
}

// --- Event Listeners ---
function setupEventListeners() {
  // Drag & drop
  dropZone.addEventListener('click', () => pdfFileInput.click());
  pdfFileInput.addEventListener('change', handleFileSelect);

  ['dragenter', 'dragover'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
      uploadFile(files[0]);
    } else {
      alert('Please drop a valid PDF file.');
    }
  });

  // Chat Form & Input
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSubmitMessage();
  });

  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmitMessage();
    }
  });

  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
  });

  // Prompt chips
  document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      chatInput.value = chip.getAttribute('data-query');
      handleSubmitMessage();
    });
  });

  // Filter buttons
  selectAllDocsBtn.addEventListener('click', () => {
    document.querySelectorAll('.doc-checkbox').forEach(cb => cb.checked = true);
    updateSelectedDocs();
  });

  deselectAllDocsBtn.addEventListener('click', () => {
    document.querySelectorAll('.doc-checkbox').forEach(cb => cb.checked = false);
    updateSelectedDocs();
  });

  // New Chat & Clear Chat
  newChatBtn.addEventListener('click', startNewChat);
  clearChatBtn.addEventListener('click', startNewChat);

  // Settings
  openSettingsBtn.addEventListener('click', openSettingsModal);
  closeSettingsBtn.addEventListener('click', closeSettingsModal);
  saveSettingsBtn.addEventListener('click', saveSettings);
  topKSlider.addEventListener('input', (e) => topKValue.textContent = e.target.value);

  // Mobile Drawer
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const sidebar = document.getElementById('sidebar');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');

  if (mobileMenuBtn && sidebar && sidebarBackdrop) {
    mobileMenuBtn.addEventListener('click', () => {
      sidebar.classList.add('open');
      sidebarBackdrop.classList.add('active');
    });

    const closeDrawer = () => {
      sidebar.classList.remove('open');
      sidebarBackdrop.classList.remove('active');
    };

    if (closeSidebarBtn) closeSidebarBtn.addEventListener('click', closeDrawer);
    sidebarBackdrop.addEventListener('click', closeDrawer);
  }
}

// --- Document Management ---
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) uploadFile(file);
}

async function uploadFile(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    alert('Only PDF files are supported.');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  uploadProgress.style.display = 'flex';
  dropZone.style.opacity = '0.5';

  try {
    const res = await fetch('/api/documents/upload', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }

    const doc = await res.json();
    await loadDocuments();

    // Auto-select newly uploaded doc
    selectedDocIds = [doc.id];
    updateDocumentListUI();
    updateFilterBadge();

  } catch (error) {
    alert('Upload error: ' + error.message);
  } finally {
    uploadProgress.style.display = 'none';
    dropZone.style.opacity = '1';
    pdfFileInput.value = '';
  }
}

async function loadDocuments() {
  try {
    const res = await fetch('/api/documents');
    const docs = await res.json();

    docCountEl.textContent = docs.length;

    if (docs.length === 0) {
      documentList.innerHTML = '<div class="empty-docs">No documents uploaded yet</div>';
      return;
    }

    documentList.innerHTML = '';
    docs.forEach(doc => {
      const item = document.createElement('div');
      item.className = 'doc-item' + (selectedDocIds.includes(doc.id) ? ' selected' : '');
      item.innerHTML = `
        <div class="doc-info" onclick="toggleDocSelection(${doc.id})">
          <input type="checkbox" class="doc-checkbox" ${selectedDocIds.includes(doc.id) ? 'checked' : ''} onclick="event.stopPropagation(); toggleDocSelection(${doc.id})">
          <i class="fa-solid fa-file-pdf doc-icon"></i>
          <div style="overflow: hidden;">
            <div class="doc-name" title="${escapeHtml(doc.title)}">${escapeHtml(doc.title)}</div>
            <div class="doc-meta">${doc.page_count} pages • ${doc.chunk_count} chunks</div>
          </div>
        </div>
        <button class="doc-delete" onclick="deleteDocument(${doc.id}, event)" title="Delete Document">
          <i class="fa-solid fa-trash-can"></i>
        </button>
      `;
      documentList.appendChild(item);
    });

    updateFilterBadge();
  } catch (err) {
    console.error('Error loading documents:', err);
  }
}

function toggleDocSelection(docId) {
  const index = selectedDocIds.indexOf(docId);
  if (index === -1) {
    selectedDocIds.push(docId);
  } else {
    selectedDocIds.splice(index, 1);
  }
  updateDocumentListUI();
  updateFilterBadge();
}

function updateSelectedDocs() {
  selectedDocIds = [];
  document.querySelectorAll('.doc-checkbox:checked').forEach(cb => {
    // get parent item's id
    const docItem = cb.closest('.doc-item');
    // We can re-trigger from UI
  });
  loadDocuments();
}

function updateDocumentListUI() {
  const checkboxes = document.querySelectorAll('.doc-checkbox');
  checkboxes.forEach((cb, idx) => {
    // Handled in loadDocuments render
  });
  loadDocuments();
}

function updateFilterBadge() {
  if (selectedDocIds.length === 0) {
    activeFilterBadge.textContent = 'Querying: All Documents';
    activeFilterBadge.style.color = 'var(--accent)';
  } else {
    activeFilterBadge.textContent = `Querying: ${selectedDocIds.length} Selected Document(s)`;
    activeFilterBadge.style.color = 'var(--success)';
  }
}

async function deleteDocument(docId, event) {
  event.stopPropagation();
  if (!confirm('Are you sure you want to delete this document and all its indexed chunks?')) return;

  try {
    const res = await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
    if (res.ok) {
      selectedDocIds = selectedDocIds.filter(id => id !== docId);
      await loadDocuments();
    }
  } catch (err) {
    alert('Error deleting document: ' + err.message);
  }
}

// --- Chat Sessions Management ---
async function loadSessions() {
  try {
    const res = await fetch('/api/chat/sessions');
    const sessions = await res.json();

    if (sessions.length === 0) {
      chatSessionsList.innerHTML = '<div class="empty-docs">No history yet</div>';
      return;
    }

    chatSessionsList.innerHTML = '';
    sessions.forEach(s => {
      const item = document.createElement('div');
      item.className = 'session-item' + (s.session_id === currentSessionId ? ' active' : '');
      item.innerHTML = `
        <span class="session-title" title="${escapeHtml(s.title)}"><i class="fa-regular fa-message"></i> ${escapeHtml(s.title)}</span>
        <button class="btn-icon" onclick="deleteSession('${s.session_id}', event)" title="Delete conversation"><i class="fa-solid fa-xmark"></i></button>
      `;
      item.addEventListener('click', () => switchSession(s.session_id, s.title));
      chatSessionsList.appendChild(item);
    });
  } catch (err) {
    console.error('Error loading sessions:', err);
  }
}

async function switchSession(sessionId, title) {
  currentSessionId = sessionId;
  document.getElementById('currentChatTitle').textContent = title || 'Document Q&A';
  welcomeBanner.style.display = 'none';

  // Highlight active session
  document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));

  // Load messages
  try {
    const res = await fetch(`/api/chat/sessions/${sessionId}`);
    const messages = await res.json();
    messagesContainer.innerHTML = '';

    messages.forEach(msg => {
      appendMessageBubble(msg.role, msg.content, msg.sources, msg.model_used);
    });

    scrollToBottom();
    await loadSessions();
  } catch (err) {
    console.error('Error loading session messages:', err);
  }
}

function startNewChat() {
  currentSessionId = null;
  document.getElementById('currentChatTitle').textContent = 'Document Q&A';
  messagesContainer.innerHTML = '';
  messagesContainer.appendChild(welcomeBanner);
  welcomeBanner.style.display = 'flex';
  document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
}

async function deleteSession(sessionId, event) {
  event.stopPropagation();
  if (!confirm('Delete this conversation history?')) return;

  try {
    await fetch(`/api/chat/sessions/${sessionId}`, { method: 'DELETE' });
    if (currentSessionId === sessionId) {
      startNewChat();
    }
    await loadSessions();
  } catch (err) {
    console.error('Error deleting session:', err);
  }
}

// --- Chat Messaging & RAG Query ---
async function handleSubmitMessage() {
  const query = chatInput.value.trim();
  if (!query || isGenerating) return;

  // Hide welcome banner if visible
  if (welcomeBanner) welcomeBanner.style.display = 'none';

  // 1. Add User Bubble
  appendMessageBubble('user', query);
  chatInput.value = '';
  chatInput.style.height = 'auto';

  // 2. Add Loading Assistant Bubble
  const botRow = document.createElement('div');
  botRow.className = 'message-row';
  botRow.innerHTML = `
    <div class="avatar bot-avatar"><i class="fa-solid fa-brain"></i></div>
    <div class="message-bubble bot-bubble" id="loadingBubble">
      <span style="color: var(--text-dim); display: inline-flex; align-items: center; gap: 8px;">
        <i class="fa-solid fa-spinner fa-spin"></i> Retrieving relevant chunks & formulating answer...
      </span>
    </div>
  `;
  messagesContainer.appendChild(botRow);
  scrollToBottom();

  isGenerating = true;
  sendBtn.disabled = true;

  try {
    const provider = providerSelect.value;
    const apiKey = (provider === 'gemini') 
      ? (geminiApiKeyInput.value.trim() || undefined)
      : (groqApiKeyInput.value.trim() || undefined);

    const payload = {
      session_id: currentSessionId,
      message: query,
      document_ids: selectedDocIds.length > 0 ? selectedDocIds : null,
      top_k: parseInt(topKSlider.value, 10),
      provider: provider,
      api_key: apiKey
    };

    const res = await fetch('/api/chat/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to generate response');
    }

    const data = await res.json();

    // Update active session id
    currentSessionId = data.session_id;

    // Remove loading bubble
    botRow.remove();

    // Append full response bubble with citations
    appendMessageBubble('assistant', data.answer, data.sources, data.model_used);
    await loadSessions();

  } catch (err) {
    botRow.remove();
    appendMessageBubble('assistant', `⚠️ **Error**: ${err.message}\n\n*Tip: Check that you uploaded a PDF document and configured your Gemini / Groq API key in Settings.*`);
  } finally {
    isGenerating = false;
    sendBtn.disabled = false;
    scrollToBottom();
  }
}

function getRelevanceBadge(score) {
  if (score === null || score === undefined) return '';
  const pct = Math.round(score * 100);
  let label = 'Relevant Context';
  let badgeColor = '#818cf8';
  if (pct >= 60) {
    label = 'Strong Match';
    badgeColor = '#34d399';
  } else if (pct >= 35) {
    label = 'Good Match';
    badgeColor = '#38bdf8';
  }
  return `<div style="font-size:0.72rem; color:${badgeColor}; margin-top:5px; font-weight:500;">
    <i class="fa-solid fa-bullseye"></i> ${label} (${pct}%)
  </div>`;
}

function appendMessageBubble(role, content, sources = null, modelUsed = null) {
  const row = document.createElement('div');
  row.className = `message-row ${role === 'user' ? 'user-row' : ''}`;

  if (role === 'user') {
    row.innerHTML = `
      <div class="message-bubble user-bubble">${escapeHtml(content)}</div>
      <div class="avatar user-avatar"><i class="fa-solid fa-user"></i></div>
    `;
  } else {
    const htmlContent = marked.parse(content);
    let citationsHtml = '';

    if (sources && sources.length > 0) {
      citationsHtml = `
        <div class="citations-box">
          <div class="citations-header" onclick="this.nextElementSibling.classList.toggle('hidden')">
            <i class="fa-solid fa-quote-left"></i> Sources & Citations (${sources.length} retrieved chunks)
          </div>
          <div class="citations-grid">
            ${sources.map(src => `
              <div class="citation-card">
                <div class="citation-card-header">
                  <span><i class="fa-solid fa-file-pdf"></i> ${escapeHtml(src.document_title)}</span>
                  <span class="citation-badge">Page ${src.page_number}</span>
                </div>
                <div class="citation-snippet">"${escapeHtml(src.snippet)}"</div>
                ${getRelevanceBadge(src.similarity_score)}
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    row.innerHTML = `
      <div class="avatar bot-avatar"><i class="fa-solid fa-brain"></i></div>
      <div class="message-bubble bot-bubble">
        <div class="markdown-body">${htmlContent}</div>
        ${citationsHtml}
        ${modelUsed ? `<div style="font-size: 0.7rem; color: var(--text-dim); margin-top: 8px;">Generated with ${modelUsed}</div>` : ''}
      </div>
    `;
  }

  messagesContainer.appendChild(row);
  scrollToBottom();
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

// --- Settings Modal ---
function openSettingsModal() {
  settingsModal.style.display = 'flex';
}

function closeSettingsModal() {
  settingsModal.style.display = 'none';
}

function saveSettings() {
  const provider = providerSelect.value;
  localStorage.setItem('rag_provider', provider);
  localStorage.setItem('gemini_api_key', geminiApiKeyInput.value.trim());
  localStorage.setItem('groq_api_key', groqApiKeyInput.value.trim());
  localStorage.setItem('rag_top_k', topKSlider.value);
  updateModelLabel();
  closeSettingsModal();
}
