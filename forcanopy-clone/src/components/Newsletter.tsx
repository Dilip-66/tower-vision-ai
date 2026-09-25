export function Newsletter() {
  return (
    <section className="mx-auto max-w-[1120px] px-4 pb-6 pt-14 sm:px-6 sm:pt-20">
      <div className="grid w-full grid-cols-1 items-center gap-6 sm:grid-cols-2 sm:gap-8">
        <div className="flex flex-col gap-2">
          <h3 className="text-[26px]! font-semibold tracking-[-0.01em] text-onbackground">
            Powered by computer vision
          </h3>
          <p className="text-onbackground opacity-80 text-pretty">
            Built from annotated visual data. The detection pipeline uses a
            YOLO-based object detection model trained on tower images that are
            labeled using LabelImg to identify the structural categories used by
            the model.
          </p>
        </div>
        <div>
          <form className="flex items-center gap-2 rounded-2xl border border-onbackground/10 bg-surface py-1.5 pl-[18px] pr-1.5">
            <input
              type="email"
              aria-label="Email address"
              autoComplete="email"
              placeholder="Email address"
              required
              className="w-full min-w-0 flex-1 bg-transparent py-2.5 text-[15px]! text-onbackground placeholder:text-onbackground/65 focus:outline-none"
              name="email_address"
              defaultValue=""
            />
            <button
              type="submit"
              className="shrink-0 cursor-pointer rounded-xl bg-cta px-[18px] py-3 text-sm font-bold text-onCta transition-colors hover:bg-accent hover:text-onAccent disabled:opacity-50"
            >
              Subscribe
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
