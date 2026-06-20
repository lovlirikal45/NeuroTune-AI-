const { app, BrowserWindow, Menu, dialog, ipcMain } = require('electron');
const path = require('path');
const { autoUpdater } = require('electron-updater');

// Configuration de l'auto-updater
autoUpdater.setFeedURL({
  provider: 'github',
  owner: 'lovlirikal45',
  repo: 'NeuroTune-AI-'
});

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    title: 'NeuroTune AI',
    icon: path.join(__dirname, 'assets/icon.ico'),
    backgroundColor: '#0a0a0f',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true
    },
    // Supprimer la barre de titre Windows pour un look custom
    frame: process.platform === 'win32' ? false : true,
    titleBarStyle: 'hidden'
  });

  // Menu personnalisé
  const menuTemplate = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open ECU File',
          accelerator: 'Ctrl+O',
          click: () => handleFileOpen()
        },
        {
          label: 'Save Project',
          accelerator: 'Ctrl+S',
          click: () => mainWindow.webContents.send('save-project')
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: 'Alt+F4',
          click: () => app.quit()
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { label: 'Undo', accelerator: 'Ctrl+Z', role: 'undo' },
        { label: 'Redo', accelerator: 'Ctrl+Y', role: 'redo' },
        { type: 'separator' },
        { label: 'Cut', accelerator: 'Ctrl+X', role: 'cut' },
        { label: 'Copy', accelerator: 'Ctrl+C', role: 'copy' },
        { label: 'Paste', accelerator: 'Ctrl+V', role: 'paste' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { label: 'Reload', accelerator: 'Ctrl+R', role: 'reload' },
        { label: 'Toggle DevTools', accelerator: 'F12', role: 'toggleDevTools' },
        { type: 'separator' },
        { label: 'Zoom In', accelerator: 'Ctrl+=', role: 'zoomIn' },
        { label: 'Zoom Out', accelerator: 'Ctrl+-', role: 'zoomOut' },
        { label: 'Reset Zoom', accelerator: 'Ctrl+0', role: 'resetZoom' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About NeuroTune AI',
          click: () => showAboutDialog()
        },
        {
          label: 'Check for Updates',
          click: () => autoUpdater.checkForUpdatesAndNotify()
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(menuTemplate);
  Menu.setApplicationMenu(menu);

  // En développement : charger depuis le serveur de dev
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    // En production : charger les fichiers buildés
    mainWindow.loadFile(path.join(__dirname, 'dist-web', 'index.html'));
  }

  // Gestion de la fermeture
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Vérifier les mises à jour
  if (process.env.NODE_ENV !== 'development') {
    autoUpdater.checkForUpdatesAndNotify();
  }
}

// Gestionnaire d'ouverture de fichier
async function handleFileOpen() {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Open ECU File',
    filters: [
      { name: 'ECU Files', extensions: ['bin', 'hex', 'srec', 'kp', 'ols', 'a2l', 'damos'] },
      { name: 'All Files', extensions: ['*'] }
    ],
    properties: ['openFile']
  });

  if (!result.canceled && result.filePaths.length > 0) {
    mainWindow.webContents.send('file-opened', result.filePaths[0]);
  }
}

// Dialogue About
function showAboutDialog() {
  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'About NeuroTune AI',
    message: 'NeuroTune AI v1.0.0',
    detail: 'Professional AI-Assisted ECU Calibration Platform\n\n' +
            '© 2024 NeuroTune AI Team\n' +
            'Built with Electron & React',
    icon: path.join(__dirname, 'assets/icon.ico')
  });
}

// Communication avec le renderer
ipcMain.handle('open-file-dialog', handleFileOpen);
ipcMain.handle('get-app-version', () => app.getVersion());
ipcMain.handle('get-user-data-path', () => app.getPath('userData'));

// Gestion des événements de l'application
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Auto-updater events
autoUpdater.on('update-available', () => {
  mainWindow.webContents.send('update-available');
});

autoUpdater.on('update-downloaded', () => {
  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'Update Ready',
    message: 'A new version has been downloaded.',
    detail: 'The application will restart to apply the update.',
    buttons: ['Restart Now', 'Later']
  }).then((result) => {
    if (result.response === 0) {
      autoUpdater.quitAndInstall();
    }
  });
});