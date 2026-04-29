const [major] = process.versions.node.split(".").map(Number);

if (Number.isNaN(major) || major < 20 || major >= 23) {
  console.error(
    [
      `Node ${process.versions.node} no es compatible con este frontend.`,
      "Usa Node 22 LTS (recomendado) o cualquier version >=20 y <23.",
      "Si usas nvm, ejecuta `nvm use` desde la raiz del proyecto y vuelve a instalar dependencias en `frontend/`.",
    ].join("\n"),
  );
  process.exit(1);
}
