import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useReducer,
} from "react";
import type { HomeAssistant, Package, Settings } from "../types";
import { fetchPackages, getSettings, refreshPackages } from "../api";
import { Header } from "./Header";
import { PackageList } from "./PackageList";
import { AddPackageDialog } from "./AddPackageDialog";
import { SettingsDrawer } from "./SettingsDrawer";
import globalStyles from "../styles/global.css?inline";

// --- State Management ---

interface AppState {
  packages: Package[];
  settings: Settings | null;
  loading: boolean;
  refreshing: boolean;
  showAddDialog: boolean;
  showSettings: boolean;
  error: string | null;
}

type AppAction =
  | { type: "SET_PACKAGES"; packages: Package[] }
  | { type: "SET_SETTINGS"; settings: Settings }
  | { type: "SET_LOADING"; loading: boolean }
  | { type: "SET_REFRESHING"; refreshing: boolean }
  | { type: "TOGGLE_ADD_DIALOG" }
  | { type: "TOGGLE_SETTINGS" }
  | { type: "SET_ERROR"; error: string | null };

const initialState: AppState = {
  packages: [],
  settings: null,
  loading: true,
  refreshing: false,
  showAddDialog: false,
  showSettings: false,
  error: null,
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "SET_PACKAGES":
      return { ...state, packages: action.packages, loading: false, error: null };
    case "SET_SETTINGS":
      return { ...state, settings: action.settings };
    case "SET_LOADING":
      return { ...state, loading: action.loading };
    case "SET_REFRESHING":
      return { ...state, refreshing: action.refreshing };
    case "TOGGLE_ADD_DIALOG":
      return { ...state, showAddDialog: !state.showAddDialog };
    case "TOGGLE_SETTINGS":
      return { ...state, showSettings: !state.showSettings };
    case "SET_ERROR":
      return { ...state, error: action.error, loading: false };
  }
}

// --- Context ---

interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  hass: HomeAssistant;
  reload: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function useAppContext(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext must be used within App");
  return ctx;
}

// --- App Component ---

interface AppProps {
  hass: HomeAssistant;
}

export function App({ hass }: AppProps) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const reload = useCallback(async () => {
    try {
      const packages = await fetchPackages(hass);
      dispatch({ type: "SET_PACKAGES", packages });
    } catch (err) {
      dispatch({ type: "SET_ERROR", error: String(err) });
    }
  }, [hass]);

  const refresh = useCallback(async () => {
    dispatch({ type: "SET_REFRESHING", refreshing: true });
    try {
      const packages = await refreshPackages(hass);
      dispatch({ type: "SET_PACKAGES", packages });
    } catch (err) {
      dispatch({ type: "SET_ERROR", error: String(err) });
    } finally {
      dispatch({ type: "SET_REFRESHING", refreshing: false });
    }
  }, [hass]);

  // Initial load.
  useEffect(() => {
    void reload();
    void getSettings(hass).then((settings) =>
      dispatch({ type: "SET_SETTINGS", settings })
    );
  }, [hass, reload]);

  const contextValue: AppContextValue = {
    state,
    dispatch,
    hass,
    reload,
    refresh,
  };

  return (
    <AppContext.Provider value={contextValue}>
      <style>{globalStyles}</style>
      <div className="paketti-tracker">
        <Header />
        <main className="paketti-main">
          <PackageList />
        </main>
        {state.showAddDialog && <AddPackageDialog />}
        {state.showSettings && <SettingsDrawer />}
      </div>
    </AppContext.Provider>
  );
}
