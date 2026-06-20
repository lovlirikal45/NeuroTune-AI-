const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Gestion de fichiers
  openFile: () => ipcRenderer.invoke('open-file-dialog'),
  onFileOpened: (callback) => ipcRenderer.on('file-opened', (_, path) => callback(path)),
  
  // Version de l'application
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getUserDataPath: () => ipcRenderer.invoke('get-user-data-path'),
  
  // Sauvegarde de projet
  onSaveProject: (callback) => ipcRenderer.on('save-project', () => callback()),
  
  // Mises à jour
  onUpdateAvailable: (callback) => ipcRenderer.on('update-available', () => callback()),
  
  // Gestion de la fenêtre
  minimizeWindow: () => ipcRenderer.send('window-minimize'),
  maximizeWindow: () => ipcRenderer.send('window-maximize'),
  closeWindow: () => ipcRenderer.send('window-close')
});