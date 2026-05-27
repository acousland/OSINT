import SwiftUI

/// Credentials live only in the Keychain. These fields write-through to it; we never read
/// secrets back into the UI (we only show whether one is set).
struct SettingsView: View {
    @State private var abrGuid = ""
    @State private var openAIKey = ""
    @State private var abrSet = Secrets.get(.abrGuid) != nil
    @State private var openAISet = Secrets.get(.openAIKey) != nil

    var body: some View {
        Form {
            Section("Australian Business Register") {
                SecureField("ABR auth GUID", text: $abrGuid)
                HStack {
                    Text(abrSet ? "✓ A GUID is stored" : "No GUID stored").font(.caption)
                        .foregroundStyle(abrSet ? .green : .secondary)
                    Spacer()
                    Button("Save") { Secrets.set(abrGuid, for: .abrGuid); abrSet = true; abrGuid = "" }
                        .disabled(abrGuid.isEmpty)
                    Button("Clear") { Secrets.clear(.abrGuid); abrSet = false }
                }
                Link("Register for a free ABR GUID", destination: URL(string: "https://abr.business.gov.au/Tools/WebServices")!)
                    .font(.caption)
            }
            Section("OpenAI") {
                SecureField("OpenAI API key", text: $openAIKey)
                HStack {
                    Text(openAISet ? "✓ A key is stored" : "No key stored").font(.caption)
                        .foregroundStyle(openAISet ? .green : .secondary)
                    Spacer()
                    Button("Save") { Secrets.set(openAIKey, for: .openAIKey); openAISet = true; openAIKey = "" }
                        .disabled(openAIKey.isEmpty)
                    Button("Clear") { Secrets.clear(.openAIKey); openAISet = false }
                }
            }
        }
        .formStyle(.grouped)
        .frame(width: 480, height: 320)
        .padding()
    }
}
