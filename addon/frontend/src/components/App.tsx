import { useCallback, useEffect, useReducer, createContext, useContext } from "react";
import { Routes, Route } from "react-router-dom";
import type { Package, Settings } from "../types";
import { fetchPackages, getSettings, refreshPackages as apiRefresh } from "../api";
import { Header } from "./Header";
import { PackageList } from "./PackageList";
import { AddPackageDialog } from "./AddPackageDialog";
import { SettingsPage } from "./SettingsPage";
import { DiscoveredPackages } from "./DiscoveredPackages";

// --- State ---

interface AppState {
  packages: Package[];
  settings: Settings | null;
  loading: boolean;
  refreshing: boolean;
  showAddDialog: boolean;
  error: string | null;
}

type AppAction =
  | { type: "SET_PACKAGES"; packages: Package[] }
  | { type: "SET_SETTINGS"; settings: Settings }
  | { type: "SET_LOADING"; loading: boolean }
  | { type: "SET_REFRESHING"; refreshing: boolean }
  | { type: "TOGGLE_ADD_DIALOG" }
  | { type: "SET_ERROR"; error: string | null };

const initialState: AppState = {
  packages: [],
  settings: null,
  loading: true,
  refreshing: false,
  showAddDialog: false,
  error: null,
};

function reducer(state: AppState, action: AppAction): AppState {
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
    case "SET_ERROR":
      return { ...state, error: action.error, loading: false };
  }
}

// --- Context ---

interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  reload: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function useAppContext(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext must be used within App");
  return ctx;
}

// --- App ---

export function App() {
  const [state, dispatch] = useReducer(reducer, initialState);

  const reload = useCallback(async () => {
    try {
      const packages = await fetchPackages();
      dispatch({ type: "SET_PACKAGES", packages });
    } catch (err) {
      dispatch({ type: "SET_ERROR", error: String(err) });
    }
  }, []);

  const refresh = useCallback(async () => {
    dispatch({ type: "SET_REFRESHING", refreshing: true });
    try {
      await apiRefresh();
      // Reload after a short delay to allow scraper to update
      setTimeout(() => void reload(), 2000);
    } catch (err) {
      dispatch({ type: "SET_ERROR", error: String(err) });
    } finally {
      dispatch({ type: "SET_REFRESHING", refreshing: false });
    }
  }, [reload]);

  useEffect(() => {
    void reload();
    void getSettings().then((s) => dispatch({ type: "SET_SETTINGS", settings: s }));
  }, [reload]);

  const contextValue: AppContextValue = { state, dispatch, reload, refresh };

  return (
    <AppContext.Provider value={contextValue}>
      <div className="paketti-tracker">
        <Header />
        <main className="paketti-main">
          <Routes>
            <Route
              path="/"
              element={
                <>
                  <DiscoveredPackages />
                  <PackageList />
                </>
              }
            />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
        {state.showAddDialog && <AddPackageDialog />}
      </div>
    </AppContext.Provider>
  );
}
