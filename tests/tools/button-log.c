// GTK event logger for the isolated button-chord regression test.
#include <gtk/gtk.h>
#include <stdio.h>

static const char* path;
static gboolean event(GtkEventControllerLegacy* controller, GdkEvent* event, gpointer data) {
    (void)controller; (void)data;
    GdkEventType type = gdk_event_get_event_type(event);
    if (type == GDK_BUTTON_PRESS || type == GDK_BUTTON_RELEASE) {
        FILE* file = fopen(path, "a");
        if (file) {
            fprintf(file, "{\"button\":%u,\"pressed\":%s}\n", gdk_button_event_get_button(event), type == GDK_BUTTON_PRESS ? "true" : "false");
            fclose(file);
        }
    }
    return FALSE;
}
static void activate(GtkApplication* app, gpointer data) {
    (void)data;
    GtkWidget* window = gtk_application_window_new(app);
    gtk_window_set_title(GTK_WINDOW(window), "ButtonLog");
    gtk_window_set_default_size(GTK_WINDOW(window), 360, 240);
    gtk_window_set_child(GTK_WINDOW(window), gtk_label_new("Mouse event test target"));
    GtkEventController* controller = gtk_event_controller_legacy_new();
    gtk_event_controller_set_propagation_phase(controller, GTK_PHASE_CAPTURE);
    g_signal_connect(controller, "event", G_CALLBACK(event), NULL);
    gtk_widget_add_controller(window, controller);
    gtk_window_present(GTK_WINDOW(window));
}
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    path = argv[1];
    GtkApplication* app = gtk_application_new("org.phantomat.ButtonLog", G_APPLICATION_NON_UNIQUE);
    g_signal_connect(app, "activate", G_CALLBACK(activate), NULL);
    int result = g_application_run(G_APPLICATION(app), 1, argv);
    g_object_unref(app);
    return result;
}
