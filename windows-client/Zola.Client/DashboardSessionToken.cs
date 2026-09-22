using System.Net.Http;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Zola.Client;

// P1-CLIENT: session token is minted by the parent and confirmed from headless GET / — P1-D01
static partial class DashboardSessionToken
{
    public static string Mint()
    {
        // P1-CLIENT: same shape the desktop passes as HERMES_DASHBOARD_SESSION_TOKEN — P1-D01
        var bytes = System.Security.Cryptography.RandomNumberGenerator.GetBytes(32);
        return Convert.ToBase64String(bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_');
    }

    public static string? ExtractFromIndexHtml(string html)
    {
        // P1-CLIENT: headless serve publishes the live token in window.__HERMES_SESSION_TOKEN__ — P1-D01
        var match = TokenAssignment().Match(html);
        if (!match.Success)
        {
            return null;
        }

        try
        {
            return JsonSerializer.Deserialize<string>(match.Groups[1].Value);
        }
        catch (JsonException)
        {
            return null;
        }
    }

    public static async Task<string?> ReadServedTokenAsync(HttpClient http, string baseUrl, CancellationToken cancellationToken)
    {
        // P1-CLIENT: GET / is the loopback token echo; it is not on the ready sentinel or in the profile — P1-D01
        using var response = await http.GetAsync(baseUrl.TrimEnd('/') + "/", cancellationToken).ConfigureAwait(false);
        var html = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode)
        {
            return null;
        }

        return ExtractFromIndexHtml(html);
    }

    [GeneratedRegex(@"window\.__HERMES_SESSION_TOKEN__\s*=\s*(""(?:\\.|[^""\\])*"")")]
    private static partial Regex TokenAssignment();
}
