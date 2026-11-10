// Encode rendered replay states as a standard H.264 MP4 using macOS AVFoundation.
import Foundation
import AVFoundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

struct Frame: Decodable { let path: String; let ticks: Int }
struct Manifest: Decodable {
    let width: Int; let height: Int; let fps: Int32; let output: String
    let slug: String; let game_id: String; let actions: Int
    let duration_seconds: Double; let frames: [Frame]
}
enum ExportError: Error { case failure(String) }
func require(_ condition: Bool, _ message: String) throws {
    if !condition { throw ExportError.failure(message) }
}
func encode(_ manifestPath: String) throws {
    let manifest=try JSONDecoder().decode(Manifest.self,from:Data(contentsOf:URL(fileURLWithPath:manifestPath)))
    let output=URL(fileURLWithPath:manifest.output)
    if FileManager.default.fileExists(atPath:output.path) { try FileManager.default.removeItem(at:output) }
    let writer=try AVAssetWriter(outputURL:output,fileType:.mp4)
    writer.shouldOptimizeForNetworkUse=true
    let input=AVAssetWriterInput(mediaType:.video,outputSettings:[
        AVVideoCodecKey:AVVideoCodecType.h264,
        AVVideoWidthKey:manifest.width,AVVideoHeightKey:manifest.height,
        AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey:4_000_000,
            AVVideoProfileLevelKey:AVVideoProfileLevelH264HighAutoLevel,
            AVVideoMaxKeyFrameIntervalKey:4]])
    input.expectsMediaDataInRealTime=false
    let attributes:[String:Any]=[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA,
        kCVPixelBufferWidthKey as String:manifest.width,kCVPixelBufferHeightKey as String:manifest.height,
        kCVPixelBufferCGImageCompatibilityKey as String:true,kCVPixelBufferCGBitmapContextCompatibilityKey as String:true]
    let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:attributes)
    writer.add(input)
    try require(writer.startWriting(),"Could not start writer: \(String(describing:writer.error))")
    writer.startSession(atSourceTime:.zero)
    var tick:Int64=0
    for frame in manifest.frames {
        try autoreleasepool {
            guard let source=CGImageSourceCreateWithURL(URL(fileURLWithPath:frame.path) as CFURL,nil),
                  let image=CGImageSourceCreateImageAtIndex(source,0,nil) else { throw ExportError.failure("Cannot load \(frame.path)") }
            try require(image.width==manifest.width && image.height==manifest.height,"Incorrect screenshot dimensions")
            var pixelBuffer:CVPixelBuffer?
            try require(CVPixelBufferCreate(kCFAllocatorDefault,manifest.width,manifest.height,kCVPixelFormatType_32BGRA,attributes as CFDictionary,&pixelBuffer)==kCVReturnSuccess,"Cannot allocate pixel buffer")
            let buffer=pixelBuffer!
            CVPixelBufferLockBaseAddress(buffer,[])
            guard let context=CGContext(data:CVPixelBufferGetBaseAddress(buffer),width:manifest.width,height:manifest.height,
                bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(buffer),space:CGColorSpaceCreateDeviceRGB(),
                bitmapInfo:CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue) else { throw ExportError.failure("Cannot create graphics context") }
            context.draw(image,in:CGRect(x:0,y:0,width:manifest.width,height:manifest.height))
            CVPixelBufferUnlockBaseAddress(buffer,[])
            for _ in 0..<frame.ticks {
                while !input.isReadyForMoreMediaData {
                    try require(writer.status == .writing,"Encoder stopped: \(String(describing:writer.error))")
                    Thread.sleep(forTimeInterval:0.005)
                }
                try require(adaptor.append(buffer,withPresentationTime:CMTime(value:tick,timescale:manifest.fps)),"Append failed: \(String(describing:writer.error))")
                tick += 1
            }
        }
    }
    writer.endSession(atSourceTime:CMTime(value:tick,timescale:manifest.fps))
    input.markAsFinished()
    let done=DispatchSemaphore(value:0)
    writer.finishWriting { done.signal() }
    done.wait()
    try require(writer.status == .completed,"Encoding failed: \(String(describing:writer.error))")
    let asset=AVURLAsset(url:output)
    guard let track=asset.tracks(withMediaType:.video).first else { throw ExportError.failure("Missing video track") }
    let duration=CMTimeGetSeconds(asset.duration)
    try require(abs(duration-manifest.duration_seconds)<0.1,"Duration mismatch")
    try require(Int(track.naturalSize.width)==manifest.width && Int(track.naturalSize.height)==manifest.height,"Video dimensions mismatch")
    // Decode the entire video, then extract a final frame for visual verification.
    let reader=try AVAssetReader(asset:asset)
    let decoded=AVAssetReaderTrackOutput(track:track,outputSettings:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA])
    reader.add(decoded);try require(reader.startReading(),"Cannot decode exported video")
    var count:Int64=0
    while decoded.copyNextSampleBuffer() != nil { count += 1 }
    try require(reader.status == .completed && count==tick,"Decoded frame count mismatch")
    let generator=AVAssetImageGenerator(asset:asset)
    generator.appliesPreferredTrackTransform=true
    let finalImage=try generator.copyCGImage(at:CMTime(seconds:duration-0.5,preferredTimescale:600),actualTime:nil)
    let finalURL=output.deletingPathExtension().appendingPathExtension("video-check.png")
    guard let destination=CGImageDestinationCreateWithURL(finalURL as CFURL,UTType.png.identifier as CFString,1,nil) else { throw ExportError.failure("Cannot create preview") }
    CGImageDestinationAddImage(destination,finalImage,nil)
    try require(CGImageDestinationFinalize(destination),"Cannot save preview")
    let report:[String:Any]=["slug":manifest.slug,"game_id":manifest.game_id,"actions":manifest.actions,
        "duration_seconds":duration,"width":manifest.width,"height":manifest.height,"codec":"H.264",
        "fps":manifest.fps,"decoded_frames":count,"all_frames_decoded":true,"audio":false]
    try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.deletingPathExtension().appendingPathExtension("video.json"))
    print("\(manifest.slug): \(duration)s, \(count) frames decoded, \(manifest.width)×\(manifest.height), \(output.path)")
}
do {
    try require(CommandLine.arguments.count>1,"Usage: encode_video MANIFEST.json [MANIFEST.json ...]")
    for argument in CommandLine.arguments.dropFirst() { try encode(argument) }
} catch {
    fputs("Video export failed: \(error)\n",stderr)
    exit(1)
}
