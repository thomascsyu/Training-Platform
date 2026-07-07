import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ThumbnailUpload } from "@/components/ThumbnailUpload";
import { API, uploadThumbnail } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  API: {
    put: jest.fn(() => Promise.resolve({ data: { message: "Course updated" } })),
  },
  uploadThumbnail: jest.fn(),
  formatError: (error) => error.message || "error",
}));

jest.mock("@/contexts/LanguageContext", () => ({
  useLanguage: () => ({ t: (key) => key }),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

describe("ThumbnailUpload", () => {
  const originalBackendUrl = process.env.REACT_APP_BACKEND_URL;

  beforeEach(() => {
    process.env.REACT_APP_BACKEND_URL = "";
    uploadThumbnail.mockReset();
    API.put.mockClear();
    URL.createObjectURL = jest.fn(() => "blob:http://localhost/preview");
    URL.revokeObjectURL = jest.fn();
  });

  afterEach(() => {
    process.env.REACT_APP_BACKEND_URL = originalBackendUrl;
  });

  it("calls onChange with the uploaded thumbnail URL", async () => {
    uploadThumbnail.mockResolvedValue({
      url: "/api/uploads/thumbnails/example.jpg",
    });
    const onChange = jest.fn();

    render(<ThumbnailUpload value="" onChange={onChange} />);

    const file = new File(["image"], "example.jpg", { type: "image/jpeg" });
    fireEvent.change(screen.getByTestId("course-thumbnail-upload-input"), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith("/api/uploads/thumbnails/example.jpg");
    });
  });

  it("persists the thumbnail to the course before calling onChange", async () => {
    uploadThumbnail.mockResolvedValue({
      url: "/api/uploads/thumbnails/example.jpg",
    });
    const onChange = jest.fn();

    render(
      <ThumbnailUpload
        value=""
        onChange={onChange}
        courseId="course-123"
      />
    );

    const file = new File(["image"], "example.jpg", { type: "image/jpeg" });
    fireEvent.change(screen.getByTestId("course-thumbnail-upload-input"), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(API.put).toHaveBeenCalledWith("/courses/course-123", {
        thumbnail_url: "/api/uploads/thumbnails/example.jpg",
      });
      expect(onChange).toHaveBeenCalledWith("/api/uploads/thumbnails/example.jpg");
    });

    expect(API.put.mock.invocationCallOrder[0]).toBeLessThan(
      onChange.mock.invocationCallOrder[0]
    );
  });

  it("calls onChange with an empty string when the thumbnail is removed", async () => {
    const onChange = jest.fn();

    render(
      <ThumbnailUpload
        value="/api/uploads/thumbnails/example.jpg"
        onChange={onChange}
        courseId="course-123"
      />
    );

    fireEvent.click(screen.getByTestId("course-thumbnail-upload-remove"));

    await waitFor(() => {
      expect(API.put).toHaveBeenCalledWith("/courses/course-123", {
        thumbnail_url: "",
      });
      expect(onChange).toHaveBeenCalledWith("");
    });
  });

  it("notifies busy state while upload and persist are in progress", async () => {
    let resolveUpload;
    uploadThumbnail.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveUpload = resolve;
        })
    );
    const onBusyChange = jest.fn();

    render(
      <ThumbnailUpload
        value=""
        onChange={jest.fn()}
        courseId="course-123"
        onBusyChange={onBusyChange}
      />
    );

    const file = new File(["image"], "example.jpg", { type: "image/jpeg" });
    fireEvent.change(screen.getByTestId("course-thumbnail-upload-input"), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(onBusyChange).toHaveBeenCalledWith(true);
    });

    await act(async () => {
      resolveUpload({ url: "/api/uploads/thumbnails/example.jpg" });
    });

    await waitFor(() => {
      expect(onBusyChange).toHaveBeenLastCalledWith(false);
    });
  });

  it("shows the stored thumbnail URL in the preview", async () => {
    render(
      <ThumbnailUpload
        value="/api/uploads/thumbnails/example.jpg"
        onChange={jest.fn()}
      />
    );

    const image = screen.getByRole("img", { name: "courses.uploadThumbnail" });
    expect(image).toHaveAttribute("src", "/api/uploads/thumbnails/example.jpg");

    await act(async () => {
      image.dispatchEvent(new Event("load"));
    });
  });
});
