import { useState, useEffect, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Award, Bot, CheckCircle, DollarSign, Download, FileText, Loader2,
  Lock, MessageSquare, Send, Video, X,
} from "lucide-react";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { useAuth } from "@/contexts/AuthContext";
import { PublicSiteHeader } from "@/components/PublicSiteHeader";
import { CourseThumbnail } from "@/components/CourseThumbnail";

export const CourseDetailPage = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [enrollment, setEnrollment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [forumPosts, setForumPosts] = useState([]);
  const [forumInput, setForumInput] = useState("");
  const [lessonProgress, setLessonProgress] = useState(null);
  const [activeLesson, setActiveLesson] = useState(null);
  const [completingLesson, setCompletingLesson] = useState(false);

  const fetchLessonProgress = useCallback(async () => {
    try {
      const { data } = await API.get(`/progress/course/${id}`);
      setLessonProgress(data);
    } catch (e) {
      console.error(e);
    }
  }, [id]);

  const fetchCourse = useCallback(async () => {
    try {
      const { data } = await API.get(`/courses/${id}`);
      setCourse(data);
      
      if (user) {
        // Check enrollment
        const enrollRes = await API.get("/enrollments/my");
        const enrolled = enrollRes.data.find(e => e.course_id === id);
        setEnrollment(enrolled);

        if (enrolled) {
          await fetchLessonProgress();
        }

        const aiAssistantEnabled = data.ai_assistant_enabled ?? true;

        // Load chat and forum
        try {
          const requests = [API.get(`/forums/${id}`)];
          if (enrolled && aiAssistantEnabled) {
            requests.unshift(API.get(`/chat/${id}/history`));
          }

          const responses = await Promise.all(requests);
          const forumRes = responses[responses.length - 1];
          setForumPosts(forumRes.data);
          if (enrolled && aiAssistantEnabled) {
            const chatRes = responses[0];
            setChatMessages(chatRes.data);
          } else {
            setChatMessages([]);
          }
        } catch (e) {
          console.error(e);
        }
      }
    } catch (e) {
      toast.error(formatError(e));
      navigate("/courses");
    } finally {
      setLoading(false);
    }
  }, [id, user, navigate, fetchLessonProgress]);

  useEffect(() => {
    fetchCourse();
  }, [fetchCourse]);

  const handleEnroll = async () => {
    if (!user) {
      navigate("/login");
      return;
    }
    
    if (!course.is_free && course.price > 0) {
      // Redirect to payment
      setEnrolling(true);
      try {
        const { data } = await API.post("/payments/checkout", {
          course_id: id,
          origin_url: window.location.origin
        });
        window.location.href = data.url;
      } catch (e) {
        toast.error(formatError(e));
        setEnrolling(false);
      }
      return;
    }
    
    setEnrolling(true);
    try {
      await API.post("/enrollments", { course_id: id });
      toast.success(t("toast.enrolledSuccess"));
      fetchCourse();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setEnrolling(false);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    if (!(course?.ai_assistant_enabled ?? true)) return;
    
    setChatLoading(true);
    try {
      const { data } = await API.post("/chat", { course_id: id, message: chatInput });
      setChatMessages([...chatMessages, 
        { role: "user", content: chatInput },
        { role: "assistant", content: data.response }
      ]);
      setChatInput("");
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setChatLoading(false);
    }
  };

  const postToForum = async () => {
    if (!forumInput.trim()) return;
    
    try {
      const { data } = await API.post("/forums/posts", { course_id: id, content: forumInput });
      setForumPosts([data, ...forumPosts]);
      setForumInput("");
      toast.success(t("toast.posted"));
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  const getVideoEmbed = (url, type) => {
    if (!url) return null;
    
    if (type === "youtube") {
      const videoId = url.match(/(?:youtu\.be\/|youtube\.com(?:\/embed\/|\/v\/|\/watch\?v=|\/watch\?.+&v=))([\w-]{11})/)?.[1];
      if (videoId) {
        return `https://www.youtube.com/embed/${videoId}`;
      }
    } else if (type === "vimeo") {
      const videoId = url.match(/vimeo\.com\/(\d+)/)?.[1];
      if (videoId) {
        return `https://player.vimeo.com/video/${videoId}`;
      }
    }
    return url;
  };

  const getLessonProgress = (lessonId) =>
    lessonProgress?.lessons?.find((l) => l.lesson_id === lessonId);

  const openLesson = (lesson) => {
    setActiveLesson(lesson);
    setActiveTab("lessons");
  };

  const markLessonComplete = async (lessonId) => {
    setCompletingLesson(true);
    try {
      const { data } = await API.post(`/progress/lessons/${lessonId}/complete`);
      setLessonProgress(data);
      toast.success(t("toast.lessonComplete"));
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setCompletingLesson(false);
    }
  };

  const updateWatchProgress = async (lessonId, watchPercent) => {
    try {
      const { data } = await API.patch(`/progress/lessons/${lessonId}`, {
        watch_percent: watchPercent,
      });
      setLessonProgress(data);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F4F5F7]">
        <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F4F5F7]">
      <PublicSiteHeader variant="compact" />

      <div className="container mx-auto px-6 md:px-12 lg:px-24 py-8" data-testid="course-detail-page">
        {/* Course Header */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2">
            {course.video_url ? (
              <div className="aspect-video bg-black rounded-sm overflow-hidden mb-6">
                <iframe
                  src={getVideoEmbed(course.video_url, course.video_type)}
                  className="w-full h-full"
                  allowFullScreen
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                />
              </div>
            ) : course.thumbnail_url ? (
              <div className="aspect-video bg-slate-100 rounded-sm overflow-hidden mb-6">
                <CourseThumbnail
                  src={course.thumbnail_url}
                  alt={course.title}
                  fallbackClassName="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#002FA7]/10 to-[#002FA7]/5"
                  fallbackIconClassName="w-12 h-12 text-[#002FA7]/40"
                />
              </div>
            ) : null}
            <h1 className="font-display text-2xl sm:text-3xl tracking-tight text-[#0A0B10] mb-4">
              {course.title}
            </h1>
            <p className="text-slate-600 mb-4">{course.description}</p>
            <div className="flex gap-2">
              {course.is_free ? (
                <Badge className="bg-green-100 text-green-700 rounded-sm">Free</Badge>
              ) : (
                <Badge className="bg-[#002FA7] text-white rounded-sm">${course.price?.toFixed(2)}</Badge>
              )}
              {course.is_private && (
                <Badge variant="secondary" className="rounded-sm">
                  <Lock className="w-3 h-3 mr-1" /> Private
                </Badge>
              )}
            </div>
          </div>

          <div>
            <Card className="card-swiss sticky top-24">
              <CardContent className="p-6">
                {enrollment ? (
                  <>
                    <div className="flex items-center gap-2 text-green-600 mb-4">
                      <CheckCircle className="w-5 h-5" />
                      <span className="font-medium">Enrolled</span>
                    </div>
                    {enrollment.completed && (
                      <div className="mb-4">
                        <p className="text-sm text-slate-600">Your Score: <span className="font-medium text-[#0A0B10]">{enrollment.score}%</span></p>
                      </div>
                    )}
                    {lessonProgress && lessonProgress.total_lessons > 0 && (
                      <div className="mb-4">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-slate-600">Lesson Progress</span>
                          <span className="font-medium">{lessonProgress.progress_percent}%</span>
                        </div>
                        <Progress value={lessonProgress.progress_percent} className="h-2" />
                        <p className="text-xs text-slate-500 mt-1">
                          {lessonProgress.completed_lessons} / {lessonProgress.total_lessons} lessons
                        </p>
                      </div>
                    )}
                    <Button 
                      onClick={() => navigate(`/certificates`)} 
                      variant="outline" 
                      className="w-full rounded-sm"
                      disabled={!enrollment.completed}
                      data-testid="view-certificate-btn"
                    >
                      <Award className="w-4 h-4 mr-2" />
                      {enrollment.completed ? t("courses.viewCertificate") : t("courses.completeToGet")}
                    </Button>
                  </>
                ) : (
                  <Button 
                    onClick={handleEnroll} 
                    className="w-full btn-primary"
                    disabled={enrolling}
                    data-testid="enroll-btn"
                  >
                    {enrolling ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : course.is_free ? (
                      t("courses.enrollFree")
                    ) : (
                      <>
                        <DollarSign className="w-4 h-4 mr-1" />
                        Buy Now - ${course.price?.toFixed(2)}
                      </>
                    )}
                  </Button>
                )}
                
                <Separator className="my-4" />
                
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Lessons</span>
                    <span className="font-medium">{course.lessons?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Quizzes</span>
                    <span className="font-medium">{course.quizzes?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Passing Score</span>
                    <span className="font-medium">{course.passing_score}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="card-swiss">
            <TabsTrigger value="overview" className="rounded-sm" data-testid="tab-overview">Overview</TabsTrigger>
            <TabsTrigger value="lessons" className="rounded-sm" data-testid="tab-lessons">Lessons</TabsTrigger>
            {enrollment && <TabsTrigger value="quizzes" className="rounded-sm" data-testid="tab-quizzes">Quizzes</TabsTrigger>}
            {enrollment && <TabsTrigger value="materials" className="rounded-sm" data-testid="tab-materials">Materials</TabsTrigger>}
            {enrollment && (course?.ai_assistant_enabled ?? true) && (
              <TabsTrigger value="chat" className="rounded-sm" data-testid="tab-chat">AI Assistant</TabsTrigger>
            )}
            {enrollment && <TabsTrigger value="forum" className="rounded-sm" data-testid="tab-forum">Forum</TabsTrigger>}
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <Card className="card-swiss">
              <CardContent className="p-6">
                <h3 className="text-lg font-medium mb-4">About this course</h3>
                <p className="text-slate-600 whitespace-pre-wrap">{course.description}</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="lessons" className="mt-6">
            {activeLesson && (
              <Card className="card-swiss mb-6">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-medium">{activeLesson.title}</h3>
                      <p className="text-sm text-slate-600">{activeLesson.description}</p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => setActiveLesson(null)} className="rounded-sm">
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                  {activeLesson.video_url && (
                    <div className="aspect-video bg-black rounded-sm overflow-hidden mb-4">
                      <iframe
                        src={getVideoEmbed(activeLesson.video_url, activeLesson.video_type || "youtube")}
                        className="w-full h-full"
                        allowFullScreen
                        title={activeLesson.title}
                      />
                    </div>
                  )}
                  {enrollment && (
                    <div className="flex items-center gap-3">
                      {getLessonProgress(activeLesson.id)?.completed ? (
                        <Badge className="bg-green-100 text-green-700 rounded-sm">
                          <CheckCircle className="w-3 h-3 mr-1" /> Completed
                        </Badge>
                      ) : (
                        <>
                          <Button
                            onClick={() => markLessonComplete(activeLesson.id)}
                            disabled={completingLesson}
                            className="btn-primary"
                            data-testid={`complete-lesson-${activeLesson.id}`}
                          >
                            {completingLesson ? <Loader2 className="w-4 h-4 animate-spin" /> : t("courses.markComplete")}
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => updateWatchProgress(activeLesson.id, 50)}
                            className="rounded-sm"
                          >
                            Log 50% watched
                          </Button>
                        </>
                      )}
                      {getLessonProgress(activeLesson.id)?.watch_percent > 0 && (
                        <span className="text-sm text-slate-500">
                          {getLessonProgress(activeLesson.id).watch_percent}% watched
                        </span>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
            <div className="space-y-4">
              {course.lessons?.length > 0 ? course.lessons.map((lesson, idx) => {
                const prog = getLessonProgress(lesson.id);
                return (
                <Card
                  key={lesson.id}
                  className={`bg-white border rounded-sm cursor-pointer transition-all ${
                    activeLesson?.id === lesson.id ? "border-[#002FA7] ring-2 ring-[#002FA7]/20" : "border-slate-200 hover:border-slate-300"
                  }`}
                  onClick={() => openLesson(lesson)}
                  data-testid={`lesson-card-${lesson.id}`}
                >
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-sm flex items-center justify-center font-medium ${
                      prog?.completed ? "bg-green-100 text-green-700" : "bg-[#002FA7]/10 text-[#002FA7]"
                    }`}>
                      {prog?.completed ? <CheckCircle className="w-5 h-5" /> : idx + 1}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">{lesson.title}</h4>
                      <p className="text-sm text-slate-600">{lesson.description}</p>
                      {prog?.watch_percent > 0 && !prog?.completed && (
                        <Progress value={prog.watch_percent} className="h-1 mt-2 w-32" />
                      )}
                    </div>
                    {lesson.video_url && <Video className="w-5 h-5 text-slate-400" />}
                  </CardContent>
                </Card>
              );}) : (
                <Card className="card-swiss">
                  <CardContent className="p-12 text-center">
                    <p className="text-slate-600">No lessons added yet</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="quizzes" className="mt-6">
            <div className="space-y-4">
              {course.quizzes?.length > 0 ? course.quizzes.map((quiz) => (
                <Card key={quiz.id} className="card-swiss">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">{quiz.title}</h4>
                      <p className="text-sm text-slate-600">Test your knowledge</p>
                    </div>
                    <Button 
                      onClick={() => navigate(`/quiz/${quiz.id}`)}
                      className="btn-primary"
                      data-testid={`take-quiz-${quiz.id}`}
                    >
                      Take Quiz
                    </Button>
                  </CardContent>
                </Card>
              )) : (
                <Card className="card-swiss">
                  <CardContent className="p-12 text-center">
                    <p className="text-slate-600">No quizzes available yet</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="materials" className="mt-6">
            <Card className="card-swiss">
              <CardContent className="p-6">
                {course.materials?.length > 0 ? (
                  <div className="space-y-3">
                    {course.materials.map((m, idx) => (
                      <a 
                        key={idx}
                        href={m.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 p-3 border border-slate-200 rounded-sm hover:bg-slate-50 transition-colors"
                        data-testid={`material-${idx}`}
                      >
                        <FileText className="w-5 h-5 text-[#002FA7]" />
                        <span className="flex-1">{m.name}</span>
                        <Download className="w-4 h-4 text-slate-400" />
                      </a>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-600 text-center py-8">No downloadable materials available</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {(course?.ai_assistant_enabled ?? true) && (
            <TabsContent value="chat" className="mt-6">
              <Card className="card-swiss">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Bot className="w-5 h-5 text-[#002FA7]" />
                    AI Course Assistant
                  </CardTitle>
                  <CardDescription>Ask questions about the course content</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-80 mb-4 border border-slate-200 rounded-sm p-4">
                    {chatMessages.length > 0 ? chatMessages.map((msg, idx) => (
                      <div key={idx} className={`mb-4 ${msg.role === "user" ? "text-right" : ""}`}>
                        <div className={`inline-block max-w-[80%] p-3 rounded-sm ${
                          msg.role === "user" ? "bg-[#002FA7] text-white" : "bg-slate-100 text-[#0A0B10]"
                        }`}>
                          {msg.content}
                        </div>
                      </div>
                    )) : (
                      <p className="text-slate-500 text-center py-8">Start a conversation with the AI assistant</p>
                    )}
                  </ScrollArea>
                  <div className="flex gap-2">
                    <Input
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder={t("chat.askQuestion")}
                      className="rounded-sm border-slate-300"
                      onKeyDown={(e) => e.key === "Enter" && sendChatMessage()}
                      data-testid="chat-input"
                    />
                    <Button
                      onClick={sendChatMessage}
                      disabled={chatLoading}
                      className="btn-primary"
                      data-testid="chat-send-btn"
                    >
                      {chatLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          )}

          <TabsContent value="forum" className="mt-6">
            <Card className="card-swiss">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-[#002FA7]" />
                  Community Forum
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-6">
                  <Textarea 
                    value={forumInput}
                    onChange={(e) => setForumInput(e.target.value)}
                    placeholder={t("forum.shareThoughts")}
                    className="rounded-sm border-slate-300 mb-2"
                    data-testid="forum-input"
                  />
                  <Button 
                    onClick={postToForum}
                    className="btn-primary"
                    data-testid="forum-post-btn"
                  >
                    Post
                  </Button>
                </div>
                
                <div className="space-y-4">
                  {forumPosts.length > 0 ? forumPosts.map((post) => (
                    <div key={post.id} className="border border-slate-200 rounded-sm p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Avatar className="w-6 h-6">
                          <AvatarFallback className="text-xs bg-[#002FA7] text-white">
                            {post.user_name?.charAt(0)?.toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <span className="font-medium text-sm">{post.user_name}</span>
                        <span className="text-xs text-slate-500">
                          {new Date(post.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-slate-700">{post.content}</p>
                      {post.replies?.length > 0 && (
                        <div className="ml-6 mt-3 space-y-2">
                          {post.replies.map((reply) => (
                            <div key={reply.id} className="border-l-2 border-slate-200 pl-3 py-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-sm">{reply.user_name}</span>
                                <span className="text-xs text-slate-500">
                                  {new Date(reply.created_at).toLocaleDateString()}
                                </span>
                              </div>
                              <p className="text-sm text-slate-600">{reply.content}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )) : (
                    <p className="text-slate-500 text-center py-8">No discussions yet. Be the first to post!</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

