import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { LoginGate } from "./components/LoginGate";
import { AskScreen } from "./screens/AskScreen";
import { EntriesScreen } from "./screens/EntriesScreen";
import { EntryDetailScreen } from "./screens/EntryDetailScreen";
import { GuidanceScreen } from "./screens/GuidanceScreen";
import { InsightsScreen } from "./screens/InsightsScreen";
import { RecordScreen } from "./screens/RecordScreen";
import { SettingsScreen } from "./screens/SettingsScreen";

export default function App() {
  return (
    <LoginGate>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<RecordScreen />} />
            <Route path="today" element={<Navigate to="/" replace />} />
            <Route path="entries" element={<EntriesScreen />} />
            <Route path="entries/:id" element={<EntryDetailScreen />} />
            <Route path="insights" element={<InsightsScreen />} />
            <Route path="ask" element={<AskScreen />} />
            <Route path="guidance" element={<GuidanceScreen />} />
            <Route path="settings" element={<SettingsScreen />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </LoginGate>
  );
}
