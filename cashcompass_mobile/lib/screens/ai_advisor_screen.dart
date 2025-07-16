import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../services/ai_advisor_service.dart';
import '../models/ai_advisor.dart';
import 'package:intl/intl.dart';

class AIAdvisorScreen extends StatefulWidget {
  const AIAdvisorScreen({Key? key}) : super(key: key);

  @override
  State<AIAdvisorScreen> createState() => _AIAdvisorScreenState();
}

class _AIAdvisorScreenState extends State<AIAdvisorScreen> {
  String? _advice;
  bool _loading = false;
  String? _error;

  Future<void> _getAdvice() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // You can customize the message sent to the backend here
      final aiAdvisor = await AIAdvisorService.sendMessage('Give me a financial overview');
      setState(() {
        _advice = aiAdvisor.advice;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  void _reset() {
    setState(() {
      _advice = null;
      _error = null;
    });
  }

  void _downloadAdvice() {
    if (_advice == null) return;
    // For now, just show a snackbar. Implement file saving/sharing as needed.
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Download feature coming soon!')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Financial Advisor'),
        backgroundColor: Colors.teal,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Gradient header card
              Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Colors.teal, Colors.tealAccent],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.08),
                      blurRadius: 12,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
                child: Column(
                  children: const [
                    Icon(Icons.auto_awesome, color: Colors.white, size: 48),
                    SizedBox(height: 12),
                    Text(
                      'AI Financial Advisor',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(height: 6),
                    Text(
                      'Get personalized financial guidance powered by advanced AI',
                      style: TextStyle(color: Colors.white70, fontSize: 16),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              // Feature highlights
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: const [
                  _FeatureIcon(icon: Icons.bolt, label: 'AI-Powered'),
                  _FeatureIcon(icon: Icons.lock, label: 'Secure'),
                  _FeatureIcon(icon: Icons.person, label: 'Personalized'),
                  _FeatureIcon(icon: Icons.download, label: 'Downloadable'),
                ],
              ),
              const SizedBox(height: 24),
              // Main advice card
              Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                elevation: 6,
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: _loading
                      ? Column(
                          children: const [
                            SizedBox(height: 32),
                            CircularProgressIndicator(),
                            SizedBox(height: 24),
                            Text('Analyzing your financial data...', style: TextStyle(fontWeight: FontWeight.bold)),
                            SizedBox(height: 32),
                          ],
                        )
                      : _error != null
                          ? Column(
                              children: [
                                const Icon(Icons.error, color: Colors.red, size: 40),
                                const SizedBox(height: 12),
                                Text('Oops! Something went wrong', style: theme.textTheme.titleMedium?.copyWith(color: Colors.red)),
                                const SizedBox(height: 8),
                                Text(_error!, style: const TextStyle(color: Colors.red)),
                                const SizedBox(height: 16),
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.refresh),
                                  label: const Text('Try Again'),
                                  onPressed: _getAdvice,
                                  style: ElevatedButton.styleFrom(backgroundColor: Colors.teal),
                                ),
                              ],
                            )
                          : _advice != null
                              ? Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text('Your Personalized Financial Insights', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                                    const Divider(height: 24),
                                    MarkdownBody(
                                      data: _advice!,
                                      styleSheet: MarkdownStyleSheet(
                                        p: const TextStyle(fontSize: 16),
                                        h2: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                                        h3: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                                      ),
                                    ),
                                  ],
                                )
                              : Column(
                                  children: const [
                                    Icon(Icons.rocket_launch, color: Colors.teal, size: 48),
                                    SizedBox(height: 16),
                                    Text('Ready to transform your financial future?', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                                    SizedBox(height: 8),
                                    Text('Click the button below to receive comprehensive, AI-powered financial advice tailored to you.', textAlign: TextAlign.center),
                                  ],
                                ),
                ),
              ),
              const SizedBox(height: 24),
              // Action buttons
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (_advice == null && !_loading)
                    ElevatedButton.icon(
                      icon: const Icon(Icons.auto_awesome),
                      label: const Text('Generate Advice'),
                      onPressed: _getAdvice,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.teal,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ),
                  if (_advice != null && !_loading) ...[
                    ElevatedButton.icon(
                      icon: const Icon(Icons.download),
                      label: const Text('Download'),
                      onPressed: _downloadAdvice,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(width: 16),
                    OutlinedButton.icon(
                      icon: const Icon(Icons.refresh),
                      label: const Text('New Analysis'),
                      onPressed: _reset,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.teal,
                        side: const BorderSide(color: Colors.teal, width: 2),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FeatureIcon extends StatelessWidget {
  final IconData icon;
  final String label;
  const _FeatureIcon({required this.icon, required this.label});
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        CircleAvatar(
          backgroundColor: Colors.teal[100],
          child: Icon(icon, color: Colors.teal[800]),
        ),
        const SizedBox(height: 6),
        Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
      ],
    );
  }
} 