export function parseMoney(value: string) {
  return value.replace(/[^\d]/g, "");
}

export function formatMoney(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") return "";
  const num =
    typeof value === "string"
      ? Number(value.replace(/[^\d]/g, ""))
      : Number(value);
  if (!Number.isFinite(num)) return "";
  return new Intl.NumberFormat("uz-UZ").format(num);
}

export function formatMoneyDisplay(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") return "-";
  const num =
    typeof value === "string"
      ? Number(value.replace(/[^\d]/g, ""))
      : Number(value);
  if (!Number.isFinite(num)) return String(value);
  return new Intl.NumberFormat("uz-UZ").format(num);
}
