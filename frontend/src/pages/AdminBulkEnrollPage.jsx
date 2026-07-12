import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Loader2 } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";

export const AdminBulkEnrollPage = () => {
  const { t } = useLanguage();
  const [courses, setCourses] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [coursesRes, usersRes] = await Promise.all([
        API.get("/courses?include_private=true"),
        API.get("/users?role=student")
      ]);
      setCourses(coursesRes.data);
      setStudents(usersRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkEnroll = async () => {
    if (!selectedCourse || selectedStudents.length === 0) {
      toast.error(t("groups.selectCourseAndStudents"));
      return;
    }
    
    setEnrolling(true);
    try {
      const { data } = await API.post("/enrollments", {
        course_id: selectedCourse,
        user_ids: selectedStudents
      });
      toast.success(data.message);
      setSelectedStudents([]);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setEnrolling(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-bulk-enroll-page">
        <PageHeader overline="Admin" title={t("dashboard.bulkEnrollTitle")} />

        {loading ? (
          <SkeletonGrid n={2} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="card-swiss">
              <CardHeader>
                <CardTitle className="font-display text-lg">{t("dashboard.selectCourse")}</CardTitle>
              </CardHeader>
              <CardContent>
                <Select value={selectedCourse} onValueChange={setSelectedCourse}>
                  <SelectTrigger className="rounded-sm" data-testid="select-course-dropdown">
                    <SelectValue placeholder={t("dashboard.chooseCourse")} />
                  </SelectTrigger>
                  <SelectContent>
                    {courses.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.title}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            <Card className="card-swiss">
              <CardHeader>
                <CardTitle className="font-display text-lg">{t("dashboard.selectStudents")}</CardTitle>
                <CardDescription>
                  {selectedStudents.length} selected
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-60 border border-slate-200 rounded-sm">
                  {students.map((s) => (
                    <label 
                      key={s.id}
                      className="flex items-center gap-3 p-3 hover:bg-slate-50 cursor-pointer border-b border-slate-100 last:border-0"
                      data-testid={`student-${s.id}`}
                    >
                      <input 
                        type="checkbox"
                        checked={selectedStudents.includes(s.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedStudents([...selectedStudents, s.id]);
                          } else {
                            setSelectedStudents(selectedStudents.filter(id => id !== s.id));
                          }
                        }}
                        className="w-4 h-4"
                      />
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="bg-[#002FA7] text-white text-sm">
                          {s.name?.charAt(0)?.toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium text-sm">{s.name}</p>
                        <p className="text-xs text-slate-500">{s.email}</p>
                      </div>
                    </label>
                  ))}
                </ScrollArea>
                <Button 
                  onClick={handleBulkEnroll}
                  disabled={enrolling || !selectedCourse || selectedStudents.length === 0}
                  className="w-full mt-4 btn-primary"
                  data-testid="bulk-enroll-btn"
                >
                  {enrolling ? <Loader2 className="w-4 h-4 animate-spin" /> : t("dashboard.enrollCount").replace("{count}", selectedStudents.length)}
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
