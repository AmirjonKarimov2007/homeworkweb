export function fileUrl(path: string) {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      return `${base}/files?path=${encodeURIComponent(path)}&token=${encodeURIComponent(token)}`;
    }
  }
  return `${base}/files?path=${encodeURIComponent(path)}`;
}
