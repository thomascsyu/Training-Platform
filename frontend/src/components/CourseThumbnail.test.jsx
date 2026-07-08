import { act, render, screen } from "@testing-library/react";
import { CourseThumbnail } from "@/components/CourseThumbnail";

describe("CourseThumbnail", () => {
  const originalBackendUrl = process.env.REACT_APP_BACKEND_URL;

  afterEach(() => {
    process.env.REACT_APP_BACKEND_URL = originalBackendUrl;
  });

  it("renders a placeholder when no src is provided", () => {
    render(<CourseThumbnail alt="ISO 9001" testId="course-thumb" />);

    expect(screen.getByTestId("course-thumb-fallback")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("renders an image when src is provided", () => {
    process.env.REACT_APP_BACKEND_URL = "";
    render(
      <CourseThumbnail
        src="/api/uploads/thumbnails/example.jpg"
        alt="ISO 9001"
        testId="course-thumb"
      />
    );

    const image = screen.getByRole("img", { name: "ISO 9001" });
    expect(image).toHaveAttribute("src", "/api/uploads/thumbnails/example.jpg");
  });

  it("falls back to a placeholder when the image fails to load", async () => {
    process.env.REACT_APP_BACKEND_URL = "";
    render(
      <CourseThumbnail
        src="/api/uploads/thumbnails/missing.jpg"
        alt="ISO 9001"
        testId="course-thumb"
      />
    );

    const image = screen.getByRole("img", { name: "ISO 9001" });

    await act(async () => {
      image.dispatchEvent(new Event("error"));
    });

    expect(screen.getByTestId("course-thumb-fallback")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("uses fallbackSrc before showing the icon placeholder", async () => {
    process.env.REACT_APP_BACKEND_URL = "";
    render(
      <CourseThumbnail
        src="/api/uploads/thumbnails/missing.jpg"
        fallbackSrc="blob:http://localhost/fallback"
        alt="ISO 9001"
        testId="course-thumb"
      />
    );

    const image = screen.getByRole("img", { name: "ISO 9001" });
    expect(image).toHaveAttribute("src", "/api/uploads/thumbnails/missing.jpg");

    await act(async () => {
      image.dispatchEvent(new Event("error"));
    });

    expect(screen.getByRole("img", { name: "ISO 9001" })).toHaveAttribute(
      "src",
      "blob:http://localhost/fallback"
    );
  });

  it("tries backend thumbnail URL if same-origin image fails", async () => {
    process.env.REACT_APP_BACKEND_URL = "http://localhost:8001";
    render(
      <CourseThumbnail
        src="/api/uploads/thumbnails/missing.jpg"
        alt="ISO 9001"
        testId="course-thumb"
      />
    );

    const image = screen.getByRole("img", { name: "ISO 9001" });
    expect(image).toHaveAttribute(
      "src",
      "/api/uploads/thumbnails/missing.jpg"
    );

    await act(async () => {
      image.dispatchEvent(new Event("error"));
    });

    expect(screen.getByRole("img", { name: "ISO 9001" })).toHaveAttribute(
      "src",
      "http://localhost:8001/api/uploads/thumbnails/missing.jpg"
    );
  });
});
