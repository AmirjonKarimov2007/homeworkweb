"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Send,
  FileText,
  Users,
  BarChart3,
  LogOut,
  Bell,
  CheckCircle,
  XCircle,
} from "lucide-react";
import Telegram from "@/lib/telegram-webapp";
import {
  getWebappData,
  getGroups,
  getUsersByGroup,
  sendNotification,
  createHomework,
  getStats,
  type WebappUserData,
  type Group,
  type Stats,
} from "@/lib/webapp-api";
import { toast } from "@/components/ui/use-toast";

type Tab = "dashboard" | "notify" | "homework" | "groups";

export default function WebappPage() {
  const searchParams = useSearchParams();
  const telegramId = parseInt(searchParams.get("telegram_id") || "0");
  const action = searchParams.get("action") || "dashboard";
  const initialGroupId = searchParams.get("group_id");

  const [user, setUser] = useState<WebappUserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>(action as Tab);
  const [stats, setStats] = useState<Stats | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(
    initialGroupId ? { id: parseInt(initialGroupId), name: "", schedule_time: null } : null
  );

  // Notification form state
  const [notifTitle, setNotifTitle] = useState("");
  const [notifBody, setNotifBody] = useState("");
  const [notifTarget, setNotifTarget] = useState<"all" | "group">("all");
  const [sendingNotif, setSendingNotif] = useState(false);

  // Homework form state
  const [hwTitle, setHwTitle] = useState("");
  const [hwDescription, setHwDescription] = useState("");
  const [hwDueDate, setHwDueDate] = useState("");
  const [hwGroup, setHwGroup] = useState<number | null>(null);
  const [creatingHw, setCreatingHw] = useState(false);

  useEffect(() => {
    Telegram.ready();
    Telegram.expand();

    if (telegramId) {
      loadData();
    }
  }, [telegramId]);

  useEffect(() => {
    if (user?.is_admin && activeTab === "dashboard") {
      loadStats();
    }
    if (user?.is_admin && (activeTab === "notify" || activeTab === "homework" || activeTab === "groups")) {
      loadGroups();
    }
  }, [activeTab, user]);

  const loadData = async () => {
    try {
      setLoading(true);
      const userData = await getWebappData(telegramId);
      setUser(userData);

      if (!userData.is_admin) {
        toast({
          title: "Ruxsat yo'q",
          description: "Bu funksiyadan faqat adminlar foydalanishi mumkin",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Xatolik",
        description: "Ma'lumotlarni yuklab bo'lmadi",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  };

  const loadGroups = async () => {
    try {
      const data = await getGroups();
      setGroups(data);
      if (initialGroupId) {
        const found = data.find((g) => g.id === parseInt(initialGroupId));
        if (found) {
          setSelectedGroup(found);
          setHwGroup(found.id);
          setNotifTarget("group");
        }
      }
    } catch (error) {
      console.error("Failed to load groups:", error);
    }
  };

  const handleSendNotification = async () => {
    if (!notifTitle.trim() || !notifBody.trim()) {
      toast({
        title: "Ma'lumot to'liq emas",
        description: "Iltimos, sarlavha va matnni kiriting",
        variant: "destructive",
      });
      return;
    }

    if (notifTarget === "group" && !selectedGroup) {
      toast({
        title: "Guruh tanlanmagan",
        description: "Iltimos, guruhni tanlang",
        variant: "destructive",
      });
      return;
    }

    try {
      setSendingNotif(true);
      const result = await sendNotification({
        sent_by: telegramId,
        target_type: notifTarget,
        target_id: notifTarget === "group" ? selectedGroup!.id : undefined,
        title: notifTitle,
        body: notifBody,
        notification_type: "announcement",
      });

      toast({
        title: "✅ Muvaffaqiyatli yuborildi",
        description: `${result.data?.count || 0} ta foydalanuvchiga e'lon yuborildi`,
      });

      setNotifTitle("");
      setNotifBody("");
    } catch (error) {
      toast({
        title: "Xatolik",
        description: "E'lon yuborib bo'lmadi",
        variant: "destructive",
      });
    } finally {
      setSendingNotif(false);
    }
  };

  const handleCreateHomework = async () => {
    if (!hwTitle.trim() || !hwDescription.trim() || !hwDueDate || !hwGroup) {
      toast({
        title: "Ma'lumot to'liq emas",
        description: "Iltimos, barcha maydonlarni to'ldiring",
        variant: "destructive",
      });
      return;
    }

    try {
      setCreatingHw(true);
      await createHomework({
        sent_by: telegramId,
        title: hwTitle,
        description: hwDescription,
        due_date: hwDueDate,
        group_id: hwGroup,
      });

      toast({
        title: "✅ Uy ishi yaratildi",
        description: "O'quvchilarga e'lon yuborildi",
      });

      setHwTitle("");
      setHwDescription("");
      setHwDueDate("");
    } catch (error) {
      toast({
        title: "Xatolik",
        description: "Uy ishi yaratib bo'lmadi",
        variant: "destructive",
      });
    } finally {
      setCreatingHw(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4" />
          <p className="text-gray-600">Yuklanmoqda...</p>
        </div>
      </div>
    );
  }

  if (!user || !user.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-center">⚠️ Ruxsat yo'q</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-gray-600 mb-4">Bu funksiyadan faqat adminlar foydalanishi mumkin.</p>
            <Button onClick={() => Telegram.close()} className="w-full">
              <LogOut className="w-4 h-4 mr-2" />
              Yopish
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-bold text-lg text-gray-900">Admin Panel</h1>
              <p className="text-sm text-gray-500">{user.full_name}</p>
            </div>
            <Button size="sm" variant="ghost" onClick={() => Telegram.close()}>
              <LogOut className="w-4 h-4" />
            </Button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-3 overflow-x-auto pb-1">
            <Button
              size="sm"
              variant={activeTab === "dashboard" ? "default" : "ghost"}
              onClick={() => setActiveTab("dashboard")}
              className={activeTab === "dashboard" ? "bg-purple-600 hover:bg-purple-700" : ""}
            >
              <BarChart3 className="w-4 h-4 mr-1" />
              Statistika
            </Button>
            <Button
              size="sm"
              variant={activeTab === "notify" ? "default" : "ghost"}
              onClick={() => setActiveTab("notify")}
              className={activeTab === "notify" ? "bg-purple-600 hover:bg-purple-700" : ""}
            >
              <Bell className="w-4 h-4 mr-1" />
              E'lon
            </Button>
            <Button
              size="sm"
              variant={activeTab === "homework" ? "default" : "ghost"}
              onClick={() => setActiveTab("homework")}
              className={activeTab === "homework" ? "bg-purple-600 hover:bg-purple-700" : ""}
            >
              <FileText className="w-4 h-4 mr-1" />
              Uy ishi
            </Button>
            <Button
              size="sm"
              variant={activeTab === "groups" ? "default" : "ghost"}
              onClick={() => setActiveTab("groups")}
              className={activeTab === "groups" ? "bg-purple-600 hover:bg-purple-700" : ""}
            >
              <Users className="w-4 h-4 mr-1" />
              Guruhlar
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 max-w-lg mx-auto">
        {/* Dashboard Tab */}
        {activeTab === "dashboard" && stats && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-gray-600">Bugungi statistika</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-sm">Uy ishi topshirganlar</span>
                  </div>
                  <Badge variant="success" className="bg-green-100 text-green-700">
                    {stats.today_homework_submitted}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <XCircle className="w-5 h-5 text-red-600" />
                    <span className="text-sm">Uy ishi topshirmaganlar</span>
                  </div>
                  <Badge variant="destructive">{stats.today_homework_not_submitted}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Send className="w-5 h-5 text-blue-600" />
                    <span className="text-sm">Bugungi tushum</span>
                  </div>
                  <Badge className="bg-blue-100 text-blue-700">
                    {stats.today_payment_received?.toLocaleString()} so'm
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-purple-600" />
                    <span className="text-sm">Jami o'quvchilar</span>
                  </div>
                  <Badge className="bg-purple-100 text-purple-700">{stats.total_students}</Badge>
                </div>
              </CardContent>
            </Card>
            <Button onClick={loadStats} className="w-full" variant="outline">
              🔄 Yangilash
            </Button>
          </div>
        )}

        {/* Notification Tab */}
        {activeTab === "notify" && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Send className="w-5 h-5" />
                E'lon yuborish
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Qaysiga yuborasiz?</label>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant={notifTarget === "all" ? "default" : "outline"}
                    onClick={() => setNotifTarget("all")}
                    className={notifTarget === "all" ? "bg-purple-600" : ""}
                  >
                    Barchaga
                  </Button>
                  <Button
                    size="sm"
                    variant={notifTarget === "group" ? "default" : "outline"}
                    onClick={() => setNotifTarget("group")}
                    className={notifTarget === "group" ? "bg-purple-600" : ""}
                  >
                    Guruhga
                  </Button>
                </div>
              </div>

              {notifTarget === "group" && (
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">Guruhni tanlang</label>
                  <select
                    value={selectedGroup?.id || ""}
                    onChange={(e) => {
                      const group = groups.find((g) => g.id === parseInt(e.target.value));
                      setSelectedGroup(group || null);
                    }}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="">Guruhni tanlang</option>
                    {groups.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Sarlavha</label>
                <Input
                  value={notifTitle}
                  onChange={(e) => setNotifTitle(e.target.value)}
                  placeholder="E'lon sarlavhasi..."
                />
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Matn</label>
                <textarea
                  value={notifBody}
                  onChange={(e) => setNotifBody(e.target.value)}
                  placeholder="E'lon matni..."
                  rows={4}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>

              <Button
                onClick={handleSendNotification}
                disabled={sendingNotif}
                className="w-full bg-purple-600 hover:bg-purple-700"
              >
                {sendingNotif ? "Yuborilmoqda..." : "📢 Yuborish"}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Homework Tab */}
        {activeTab === "homework" && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Uy ishi yaratish
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Guruh</label>
                <select
                  value={hwGroup || ""}
                  onChange={(e) => setHwGroup(parseInt(e.target.value) || null)}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="">Guruhni tanlang</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Sarlavha</label>
                <Input
                  value={hwTitle}
                  onChange={(e) => setHwTitle(e.target.value)}
                  placeholder="Uy ishi sarlavhasi..."
                />
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Tavsif</label>
                <textarea
                  value={hwDescription}
                  onChange={(e) => setHwDescription(e.target.value)}
                  placeholder="Uy ishi tavsifi..."
                  rows={4}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Muddati</label>
                <Input
                  type="datetime-local"
                  value={hwDueDate}
                  onChange={(e) => setHwDueDate(e.target.value)}
                />
              </div>

              <Button
                onClick={handleCreateHomework}
                disabled={creatingHw}
                className="w-full bg-purple-600 hover:bg-purple-700"
              >
                {creatingHw ? "Yaratilmoqda..." : "📝 Yaratish"}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Groups Tab */}
        {activeTab === "groups" && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Guruhlar
              </CardTitle>
            </CardHeader>
            <CardContent>
              {groups.length === 0 ? (
                <p className="text-center text-gray-500 py-8">Guruhlar topilmadi</p>
              ) : (
                <div className="space-y-2">
                  {groups.map((group) => (
                    <div
                      key={group.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <p className="font-medium">{group.name}</p>
                        {group.schedule_time && (
                          <p className="text-sm text-gray-500">{group.schedule_time}</p>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedGroup(group);
                          setHwGroup(group.id);
                          setActiveTab("notify");
                        }}
                      >
                        <Bell className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
