type UIStateHandler = (ui: any, metadata: any) => any;

export const UI_STATE_HANDLERS: Record<string, UIStateHandler> = {
  mcq: (ui: any, metadata: any) => ({
    ...ui,
    state: "completed",
    result: metadata,
  }),

  // future:
  // timeslot_picker: ...
  // confirmation: ...
};
